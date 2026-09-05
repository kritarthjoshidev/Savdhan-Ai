"""Local camera registry and controlled border-processing sessions.

Camera URLs can contain credentials, so they stay in the local ignored data
folder and are never returned to the browser. The frontend talks only in terms
of camera IDs.
"""

from __future__ import annotations

import json
import ipaddress
import re
import socket
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import cv2

from app.core.config import settings


def _safe_id(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip().lower()).strip("-")
    if not normalized:
        raise ValueError("Camera ID must contain letters or numbers")
    return normalized[:80]


def _mask_url(url: str) -> str:
    parts = urlsplit(url)
    host = parts.hostname or "camera"
    if parts.port:
        host = f"{host}:{parts.port}"
    return urlunsplit((parts.scheme, host, parts.path, "", ""))


class CameraManager:
    def __init__(self) -> None:
        root = Path(settings.LOCAL_STORAGE_DIR)
        if not root.is_absolute():
            root = Path(__file__).resolve().parents[2] / root
        root.mkdir(parents=True, exist_ok=True)
        self.file = root / "cameras.json"
        self._lock = threading.RLock()
        self._sessions: dict[str, dict[str, Any]] = {}
        self._cameras = self._load()

    def _load(self) -> dict[str, dict[str, Any]]:
        try:
            parsed = json.loads(self.file.read_text(encoding="utf-8"))
            return parsed if isinstance(parsed, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _save(self) -> None:
        temp = self.file.with_suffix(".tmp")
        temp.write_text(json.dumps(self._cameras, indent=2), encoding="utf-8")
        temp.replace(self.file)

    @staticmethod
    def validate_url(stream_url: str) -> None:
        value = stream_url.strip()
        parts = urlsplit(value)
        scheme = parts.scheme.lower()
        if scheme not in {"rtsp", "http", "https"}:
            raise ValueError("Use an rtsp://, http://, or https:// camera stream URL")
        if not parts.hostname:
            raise ValueError("Camera URL must include a host, for example rtsp://192.168.1.194:554/stream")
        if parts.username or parts.password:
            # urlsplit can parse credentials, but reject malformed percent-free
            # values only through its standard port/hostname access below.
            pass
        try:
            hostname = parts.hostname
            if re.fullmatch(r"[0-9.]+", hostname):
                ipaddress.ip_address(hostname)
            if parts.port is not None and not 1 <= parts.port <= 65535:
                raise ValueError("Camera URL port must be between 1 and 65535")
        except ValueError as exc:
            if "port" in str(exc).lower():
                raise
            raise ValueError(
                f"Invalid camera host '{hostname}'. Check the IP address; each IPv4 part must be 0-255."
            ) from exc
        if scheme == "rtsp" and not parts.path:
            raise ValueError(
                "RTSP URL needs the camera stream path, for example rtsp://192.168.1.194:554/stream"
            )

    @staticmethod
    def check_rtsp_endpoint(stream_url: str, timeout: float = 5.0) -> None:
        parts = urlsplit(stream_url.strip())
        port = parts.port or 554
        try:
            with socket.create_connection((parts.hostname, port), timeout=timeout):
                return
        except OSError as exc:
            raise ConnectionError(
                f"RTSP camera is not reachable at {parts.hostname}:{port}. "
                "Check that the camera is powered on and both devices share the same network."
            ) from exc

    def add(self, camera_id: str, name: str, stream_url: str) -> dict[str, Any]:
        camera_id = _safe_id(camera_id)
        self.validate_url(stream_url)
        with self._lock:
            if camera_id in self._cameras:
                raise ValueError("A camera with this ID already exists")
            self._cameras[camera_id] = {
                "camera_id": camera_id,
                "name": name.strip() or camera_id,
                "stream_url": stream_url.strip(),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._save()
        return self.info(camera_id)

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            return [self.info(camera_id) for camera_id in self._cameras]

    def get(self, camera_id: str) -> dict[str, Any] | None:
        with self._lock:
            camera = self._cameras.get(camera_id)
            return dict(camera) if camera else None

    def info(self, camera_id: str) -> dict[str, Any]:
        with self._lock:
            camera = self._cameras.get(camera_id)
            if not camera:
                raise KeyError(camera_id)
            session = self._sessions.get(camera_id, {})
            return {
                "camera_id": camera["camera_id"],
                "name": camera["name"],
                "stream_url_masked": _mask_url(camera["stream_url"]),
                "created_at": camera.get("created_at"),
                "status": session.get("status", "idle"),
                "last_error": session.get("last_error"),
            }

    def test(self, stream_url: str) -> dict[str, Any]:
        self.validate_url(stream_url)
        if stream_url.strip().lower().startswith("rtsp://"):
            self.check_rtsp_endpoint(stream_url)
        cap = cv2.VideoCapture(stream_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
        try:
            ok, frame = cap.read()
            if not ok or frame is None:
                return {"ok": False, "message": "Could not read a frame from this camera URL"}
            height, width = frame.shape[:2]
            fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
            return {
                "ok": True,
                "message": "Camera stream is reachable",
                "resolution": f"{width}x{height}",
                "fps": round(fps, 1),
            }
        finally:
            cap.release()

    def start(
        self,
        camera_id: str,
        analysis_mode: str = "auto",
        confidence_threshold: float = 0.35,
        sample_every_n_frames: int = 8,
        fence_y_ratio: float = 0.5,
        accident_threshold: float = 0.52,
    ) -> dict[str, Any]:
        camera = self.get(camera_id)
        if not camera:
            raise KeyError(camera_id)
        with self._lock:
            existing = self._sessions.get(camera_id)
            if existing and existing["thread"].is_alive():
                return self.info(camera_id)
            stop_event = threading.Event()
            session = {
                "status": "starting",
                "stop_event": stop_event,
                "last_error": None,
            }
            thread = threading.Thread(
                target=self._run,
                args=(
                    camera_id,
                    camera["stream_url"],
                    stop_event,
                    confidence_threshold,
                    sample_every_n_frames,
                    fence_y_ratio,
                    analysis_mode,
                    accident_threshold,
                ),
                daemon=True,
                name=f"border-camera-{camera_id}",
            )
            session["thread"] = thread
            self._sessions[camera_id] = session
            thread.start()
        return self.info(camera_id)

    def _run(
        self,
        camera_id: str,
        stream_url: str,
        stop_event: threading.Event,
        confidence_threshold: float,
        sample_every_n_frames: int,
        fence_y_ratio: float,
        analysis_mode: str,
        accident_threshold: float,
    ) -> None:
        with self._lock:
            self._sessions[camera_id]["status"] = "running"
        try:
            from app.workers.detection_worker import DetectionWorker

            worker = DetectionWorker(
                fence_y_ratio=fence_y_ratio,
                analysis_mode=analysis_mode,
                accident_threshold=accident_threshold,
            )
            worker.process_video_stream(
                video_source=stream_url,
                cam_id=camera_id,
                conf_threshold=confidence_threshold,
                sample_every_n_frames=sample_every_n_frames,
                stop_event=stop_event,
            )
            with self._lock:
                self._sessions[camera_id]["status"] = "stopped" if stop_event.is_set() else "disconnected"
        except Exception as exc:
            with self._lock:
                self._sessions[camera_id]["status"] = "error"
                self._sessions[camera_id]["last_error"] = str(exc)

    def stop(self, camera_id: str) -> dict[str, Any]:
        with self._lock:
            session = self._sessions.get(camera_id)
            if session and session.get("thread").is_alive():
                session["status"] = "stopping"
                session["stop_event"].set()
        return self.info(camera_id)

    def delete(self, camera_id: str) -> None:
        self.stop(camera_id)
        with self._lock:
            if camera_id not in self._cameras:
                raise KeyError(camera_id)
            del self._cameras[camera_id]
            self._save()


_manager: CameraManager | None = None


def get_camera_manager() -> CameraManager:
    global _manager
    if _manager is None:
        _manager = CameraManager()
    return _manager
