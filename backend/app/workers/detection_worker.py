"""Domain-aware incident worker for border intrusion and traffic accidents."""

from __future__ import annotations

import asyncio
import logging
from collections import Counter
from typing import Literal, Optional

import cv2
import numpy as np

from app.db import crud
from app.db.database import SessionLocal
from app.db.models import Snapshot
from app.ml.border_analytics import CameraFences
from app.ml.motion_gate import MotionGate
from app.ml.reid_embed import ReIDEmbedding
from app.ml.scene_events import (
    EVENT_BORDER_INTRUSION,
    EVENT_TRAFFIC_ACCIDENT,
    IncidentDeduplicator,
    SceneEventClassifier,
    TrafficAccidentState,
)
from app.ml.yolo_infer import AUTO_CLASSES, DEFAULT_BORDER_CLASSES, TRAFFIC_CLASSES, YOLOInference
from app.services.evidence import EvidenceRecorder
from app.services.storage import get_storage
from app.core.events import publish_alert

logger = logging.getLogger(__name__)

AnalysisMode = Literal["border", "traffic", "auto"]


class DetectionWorker:
    """Process a feed and create semantically meaningful, non-duplicate incidents."""

    def __init__(
        self,
        model_path: str = "yolov8s-world.pt",
        fence_y_ratio: float = 0.50,
        analysis_mode: AnalysisMode = "auto",
        accident_threshold: float = 0.52,
    ):
        if analysis_mode not in {"border", "traffic", "auto"}:
            raise ValueError("analysis_mode must be border, traffic, or auto")
        self.analysis_mode = analysis_mode
        self.model_path = model_path
        self.yolo: Optional[YOLOInference] = None
        # Traffic scenes are classified by CLIP and do not force an unnecessary
        # YOLO-World download. Border mode loads YOLO immediately.
        if analysis_mode == "border":
            self._ensure_yolo("border")
        self.storage = get_storage()
        self.db = SessionLocal()
        self.virtual_fences = CameraFences(fence_y_ratio=fence_y_ratio)
        self.motion_gate = MotionGate()
        self.reid = ReIDEmbedding()
        self.scene_classifier = SceneEventClassifier()
        self.traffic_state = TrafficAccidentState(threshold=accident_threshold)
        self.deduplicator = IncidentDeduplicator()

    @staticmethod
    def _classes_for_mode(mode: AnalysisMode) -> list[str]:
        if mode == "border":
            return DEFAULT_BORDER_CLASSES
        if mode == "traffic":
            return TRAFFIC_CLASSES
        return AUTO_CLASSES

    def _ensure_yolo(self, mode: AnalysisMode) -> YOLOInference:
        classes = self._classes_for_mode(mode)
        if self.yolo is None:
            self.yolo = YOLOInference(self.model_path, classes=classes)
        elif self.yolo.classes != classes:
            self.yolo.set_classes(classes)
        return self.yolo

    def process_video_stream(
        self,
        video_source: str,
        cam_id: str,
        conf_threshold: float = 0.35,
        sample_every_n_frames: int = 5,
        stop_event=None,
    ) -> dict | None:
        """Process local video, RTSP, or HTTP camera stream.

        ``auto`` locks the first CLIP scene decision to traffic or border so a
        road-accident video cannot accidentally be evaluated by a tripwire.
        """
        cap = None
        try:
            cap = cv2.VideoCapture(video_source)
            if not cap.isOpened():
                logger.error("Failed to open video source: %s", video_source)
                return None

            frame_count = 0
            analyzed_frames = 0
            motion_frames = 0
            source_fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
            evidence = EvidenceRecorder(self.storage, cam_id, source_fps)
            class_counts = Counter()
            event_counts = Counter()
            resolved_mode: Optional[str] = self.analysis_mode if self.analysis_mode != "auto" else None
            last_semantic: Optional[dict] = None

            while True:
                if stop_event is not None and stop_event.is_set():
                    logger.info("Stopping processing for %s on operator request", cam_id)
                    break
                ok, frame = cap.read()
                if not ok or frame is None:
                    break
                frame_count += 1

                for incident_id, evidence_meta in evidence.observe(frame, frame_count):
                    self._complete_evidence(incident_id, evidence_meta)

                if frame_count % sample_every_n_frames:
                    continue

                enhanced = YOLOInference.enhance_low_light(frame)
                analyzed_frames += 1
                detections: list[dict] = []

                # Semantic scoring is sampled every second analyzed frame on CPU.
                # It runs immediately on auto mode so the mode can be resolved.
                semantic_due = resolved_mode in {None, "traffic"} and (
                    analyzed_frames == 1 or analyzed_frames % 2 == 0
                )
                if semantic_due:
                    last_semantic = self.scene_classifier.classify(enhanced)
                    if resolved_mode is None and last_semantic.get("available"):
                        resolved_mode = last_semantic["domain"]
                        logger.info("Auto profile resolved %s as %s", cam_id, resolved_mode)
                    elif resolved_mode is None:
                        # Safe fallback when the optional CLIP weights are absent.
                        resolved_mode = "border"

                active_mode = resolved_mode or "border"
                if active_mode == "traffic":
                    # Keep object evidence alongside the scene score. A crash
                    # is classified semantically, but review still needs the
                    # vehicles involved when available.
                    detections = self._ensure_yolo("traffic").process_frame(
                        enhanced, conf_threshold, track=True
                    )
                    class_counts.update(item["class_name"] for item in detections)
                    # Accidents can become visually static after the impact;
                    # never gate a traffic scene behind background motion.
                    if last_semantic and semantic_due and self.traffic_state.observe(last_semantic):
                        track_id = "traffic-scene"
                        if self.deduplicator.claim(
                            cam_id, EVENT_TRAFFIC_ACCIDENT, track_id, frame_count, source_fps
                        ):
                            primary = self._primary_vehicle(detections)
                            semantic_for_event = dict(last_semantic)
                            if primary:
                                semantic_for_event["detection"] = primary
                            self._handle_event(
                                frame=enhanced,
                                cam_id=cam_id,
                                detection=primary,
                                frame_id=frame_count,
                                event_type=EVENT_TRAFFIC_ACCIDENT,
                                track_id=track_id,
                                evidence=evidence,
                                semantic=semantic_for_event,
                            )
                            event_counts[EVENT_TRAFFIC_ACCIDENT] += 1
                    continue

                motion = self.motion_gate.update(enhanced)
                if not motion.active:
                    continue
                motion_frames += 1
                detections = self._ensure_yolo("border").process_frame(
                    enhanced, conf_threshold, track=True
                )
                class_counts.update(item["class_name"] for item in detections)

                # Border profile: only a person moving through the directional
                # virtual fence can create an intrusion incident.
                for detection in detections:
                    if detection["class_name"] != "person":
                        continue
                    border_state = self.virtual_fences.update(
                        cam_id,
                        detection["bbox"],
                        frame.shape[0],
                        track_hint=detection.get("track_id"),
                    )
                    track_id = border_state["track_id"]
                    if border_state["intrusion"] and self.deduplicator.claim(
                        cam_id, EVENT_BORDER_INTRUSION, track_id, frame_count, source_fps
                    ):
                        self._handle_event(
                            frame=enhanced,
                            cam_id=cam_id,
                            detection=detection,
                            frame_id=frame_count,
                            event_type=EVENT_BORDER_INTRUSION,
                            track_id=track_id,
                            evidence=evidence,
                            border_state=border_state,
                        )
                        event_counts[EVENT_BORDER_INTRUSION] += 1

            for incident_id, evidence_meta in evidence.finish_all():
                self._complete_evidence(incident_id, evidence_meta)

            return {
                "frames_read": frame_count,
                "motion_frames": motion_frames,
                "frames_analyzed": analyzed_frames,
                "total_detections": sum(class_counts.values()),
                "class_counts": dict(class_counts),
                "events": dict(event_counts),
                "analysis_mode_requested": self.analysis_mode,
                "analysis_mode_resolved": resolved_mode or "border",
            }
        except Exception:
            logger.exception("Error processing video stream from %s", cam_id)
            return None
        finally:
            if cap is not None:
                cap.release()
            self.db.close()

    @staticmethod
    def _primary_vehicle(detections: list[dict]) -> Optional[dict]:
        vehicle_names = {"car", "truck", "bus", "motorcycle", "bicycle", "vehicle"}
        vehicles = [item for item in detections if item["class_name"] in vehicle_names]
        return max(vehicles, key=lambda item: item["confidence"], default=None)

    def _handle_event(
        self,
        frame: np.ndarray,
        cam_id: str,
        detection: Optional[dict],
        frame_id: int,
        event_type: str,
        track_id: str,
        evidence: EvidenceRecorder,
        border_state: Optional[dict] = None,
        semantic: Optional[dict] = None,
    ) -> None:
        """Save one named event with evidence and a human-readable explanation."""
        try:
            height, width = frame.shape[:2]
            bbox = detection["bbox"] if detection else [width / 2, height / 2, width, height]
            confidence = (
                float((semantic or {}).get("scores", {}).get("traffic_accident", 0.0))
                if event_type == EVENT_TRAFFIC_ACCIDENT
                else float((detection or {}).get("confidence", 0.0))
            )
            snapshot_key = self.storage.save_snapshot(
                cam_id,
                frame,
                bbox if event_type == EVENT_BORDER_INTRUSION else None,
                timestamp=f"{event_type.lower()}_{frame_id}",
            )

            reid_meta = {"backend": "not_applicable", "matched_incident_id": None, "similarity": None}
            embedding = None
            if event_type == EVENT_BORDER_INTRUSION and detection:
                person_crop = self._ensure_yolo("border").crop_detection(frame, bbox)
                embedding = self.reid.get_embedding(person_crop)
                reid_match = self._find_reid_match(embedding)
                reid_meta = {
                    "backend": self.reid.backend,
                    "matched_incident_id": reid_match["incident_id"] if reid_match else None,
                    "similarity": reid_match["similarity"] if reid_match else None,
                }

            explanation = self._explanation(event_type, confidence, semantic, border_state)
            meta = {
                "event_type": event_type,
                "ai_finding": explanation,
                "frame_id": frame_id,
                "detection": detection or {"class_name": "scene", "bbox": bbox},
                "analysis_mode": "traffic" if event_type == EVENT_TRAFFIC_ACCIDENT else "border",
                "low_light_enhancement": "CLAHE",
                "reid": reid_meta,
            }
            if border_state:
                meta["virtual_fence"] = border_state
            if semantic:
                meta["scene_classification"] = semantic

            incident = crud.create_incident(
                self.db,
                source_cam=cam_id,
                bbox=bbox,
                snapshot_path=snapshot_key,
                confidence=confidence,
                track_id=track_id,
                meta=meta,
            )
            crud.create_snapshot(
                self.db,
                incident_id=incident.id,
                minio_key=snapshot_key,
                embedding=embedding.tolist() if embedding is not None else None,
            )

            try:
                annotated = self._annotate_evidence_frame(frame, detection, event_type, confidence, border_state)
                initial_evidence = evidence.begin(incident.id, frame_id, annotated)
            except Exception as evidence_error:
                logger.exception("Could not start evidence capture for incident %s", incident.id)
                initial_evidence = {"status": "unavailable", "error": str(evidence_error), "event_frame_id": frame_id}
            incident = crud.update_incident_meta(self.db, incident.id, {"evidence": initial_evidence})

            asyncio.run(
                publish_alert(
                    "incidents",
                    {
                        "event": event_type,
                        "incident_id": incident.id,
                        "source_cam": cam_id,
                        "confidence": confidence,
                        "track_id": track_id,
                        "summary": explanation["summary"],
                        "evidence_status": initial_evidence["status"],
                    },
                )
            )
            logger.info("Created %s incident %s from %s", event_type, incident.id, cam_id)
        except Exception:
            logger.exception("Failed to create %s incident for %s", event_type, cam_id)

    @staticmethod
    def _explanation(event_type: str, confidence: float, semantic: Optional[dict], border_state: Optional[dict]) -> dict:
        if event_type == EVENT_TRAFFIC_ACCIDENT:
            scores = (semantic or {}).get("scores", {})
            normal_score = float(scores.get("normal_traffic", 0.0))
            detection = (semantic or {}).get("detection") or {}
            involved = detection.get("class_name") or "vehicle scene"
            return {
                "finding_code": EVENT_TRAFFIC_ACCIDENT,
                "label": "Traffic accident suspected",
                "summary": (
                    f"Traffic accident suspected involving {involved}: "
                    f"accident score {confidence:.0%}; normal-traffic score {normal_score:.0%}. "
                    "Operator review required."
                ),
                "reason": "Two consecutive zero-shot scene classifications indicated a crash scene.",
            }
        direction = "above to below"
        if border_state and border_state.get("direction"):
            direction = str(border_state["direction"]).replace("_", " ")
        return {
            "finding_code": EVENT_BORDER_INTRUSION,
            "label": "Border intrusion detected",
            "summary": f"Border intrusion detected: a tracked person crossed the virtual fence {direction}.",
            "reason": "Directional tripwire crossing was confirmed for one tracked person.",
        }

    @staticmethod
    def _annotate_evidence_frame(
        frame: np.ndarray,
        detection: Optional[dict],
        event_type: str,
        confidence: float,
        border_state: Optional[dict],
    ) -> np.ndarray:
        annotated = frame.copy()
        color = (0, 165, 255) if event_type == EVENT_TRAFFIC_ACCIDENT else (0, 0, 255)
        label = ("TRAFFIC ACCIDENT" if event_type == EVENT_TRAFFIC_ACCIDENT else "BORDER INTRUSION") + f" {confidence:.0%}"
        if border_state:
            fence_y = int(border_state.get("fence_y", annotated.shape[0] // 2))
            cv2.line(annotated, (0, fence_y), (annotated.shape[1], fence_y), (0, 0, 255), 2)
        if detection:
            x_center, y_center, box_width, box_height = detection["bbox"]
            x1, y1 = max(0, int(x_center - box_width / 2)), max(0, int(y_center - box_height / 2))
            x2 = min(annotated.shape[1] - 1, int(x_center + box_width / 2))
            y2 = min(annotated.shape[0] - 1, int(y_center + box_height / 2))
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            text_pos = (x1, max(22, y1 - 8))
        else:
            text_pos = (16, 30)
        cv2.putText(annotated, label, text_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
        return annotated

    def _complete_evidence(self, incident_id: int, evidence_meta: dict) -> None:
        incident = crud.update_incident_meta(self.db, incident_id, {"evidence": evidence_meta})
        if not incident:
            return
        try:
            asyncio.run(
                publish_alert(
                    "incidents",
                    {
                        "event": "incident_evidence_ready",
                        "incident_id": incident_id,
                        "source_cam": incident.source_cam,
                        "evidence_status": evidence_meta.get("status"),
                    },
                )
            )
        except Exception as exc:
            logger.warning("Could not publish evidence-ready alert: %s", exc)

    def _find_reid_match(self, embedding: np.ndarray, threshold: float = 0.70) -> Optional[dict]:
        snapshots = (
            self.db.query(Snapshot)
            .filter(Snapshot.embedding.is_not(None))
            .order_by(Snapshot.created_at.desc())
            .limit(200)
            .all()
        )
        gallery = [np.asarray(item.embedding, dtype=np.float32) for item in snapshots]
        match_index = self.reid.match_embedding(embedding, gallery, threshold)
        if match_index is None:
            return None
        matched = snapshots[match_index]
        return {
            "incident_id": matched.incident_id,
            "similarity": round(self.reid.compute_similarity(embedding, gallery[match_index]), 4),
        }


_detection_worker: Optional[DetectionWorker] = None


def get_detection_worker(model_path: str = "yolov8s-world.pt") -> DetectionWorker:
    global _detection_worker
    if _detection_worker is None:
        _detection_worker = DetectionWorker(model_path)
    return _detection_worker
