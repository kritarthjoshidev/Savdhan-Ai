"""Capture short, reviewable evidence around an intrusion event."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class PendingEvidence:
    incident_id: int
    event_frame_id: int
    event_sample_index: int
    frames: list[np.ndarray]
    evidence: dict[str, Any]
    post_samples_needed: int
    post_samples_collected: int = 0


class EvidenceRecorder:
    """Keep a small rolling buffer and finish a clip after an incident.

    Frames are sampled at a deliberately low FPS. This gives an operator useful
    before/after context while keeping memory and stored-video size reasonable
    for a normal laptop or an RTSP phone camera.
    """

    def __init__(
        self,
        storage,
        camera_id: str,
        source_fps: float,
        pre_seconds: float = 2.0,
        post_seconds: float = 3.0,
        capture_fps: float = 8.0,
    ):
        self.storage = storage
        self.camera_id = camera_id
        self.capture_fps = max(1.0, min(float(capture_fps), 10.0))
        self.source_fps = source_fps if source_fps and source_fps > 1 else 25.0
        self.sample_stride = max(1, round(self.source_fps / self.capture_fps))
        self.pre_samples = max(1, round(pre_seconds * self.capture_fps))
        self.post_samples = max(1, round(post_seconds * self.capture_fps))
        self.before = deque(maxlen=self.pre_samples)
        self.pending: list[PendingEvidence] = []

    def observe(self, frame: np.ndarray, frame_id: int) -> list[tuple[int, dict[str, Any]]]:
        """Store a low-rate frame and return evidence records that just finished."""
        if frame_id % self.sample_stride:
            return []

        sample = frame.copy()
        self.before.append(sample)
        completed: list[tuple[int, dict[str, Any]]] = []
        still_pending: list[PendingEvidence] = []

        for item in self.pending:
            item.frames.append(sample.copy())
            item.post_samples_collected += 1
            if item.post_samples_collected >= item.post_samples_needed:
                completed.append((item.incident_id, self._finalize(item)))
            else:
                still_pending.append(item)
        self.pending = still_pending
        return completed

    def begin(
        self,
        incident_id: int,
        event_frame_id: int,
        annotated_event_frame: np.ndarray,
    ) -> dict[str, Any]:
        """Save immediate evidence and begin collecting the following seconds."""
        samples = [frame.copy() for frame in self.before]
        if not samples:
            samples = [annotated_event_frame.copy()]
        else:
            # The context clip should visibly mark the actual trigger frame.
            samples[-1] = annotated_event_frame.copy()
        event_index = len(samples) - 1

        detected_key = self.storage.save_evidence_frame(
            self.camera_id, incident_id, "detected", annotated_event_frame
        )
        frames: list[dict[str, Any]] = []

        # Two frames just before the trigger make the human review meaningful
        # even while the rest of the clip is still being recorded.
        for ordinal, index in enumerate(self._pre_indices(event_index), start=1):
            key = self.storage.save_evidence_frame(
                self.camera_id, incident_id, f"before_{ordinal}", samples[index]
            )
            frames.append(
                {
                    "label": f"{self._relative_seconds(index - event_index)}s before",
                    "relative_seconds": self._relative_seconds(index - event_index),
                    "key": key,
                }
            )

        evidence: dict[str, Any] = {
            "status": "recording",
            "event_frame_id": event_frame_id,
            "capture_fps": self.capture_fps,
            "detected_frame": {"key": detected_key, "label": "Detection frame"},
            "frames": frames,
            "clip": None,
        }
        self.pending.append(
            PendingEvidence(
                incident_id=incident_id,
                event_frame_id=event_frame_id,
                event_sample_index=event_index,
                frames=samples,
                evidence=evidence,
                post_samples_needed=self.post_samples,
            )
        )
        return evidence

    def finish_all(self) -> list[tuple[int, dict[str, Any]]]:
        """Flush partial clips when a file ends or a camera session is stopped."""
        completed = [(item.incident_id, self._finalize(item)) for item in self.pending]
        self.pending = []
        return completed

    def _finalize(self, item: PendingEvidence) -> dict[str, Any]:
        evidence = {**item.evidence, "frames": list(item.evidence.get("frames", []))}
        post_start = item.event_sample_index + 1
        post_count = max(0, len(item.frames) - post_start)
        for ordinal, index in enumerate(self._post_indices(post_start, post_count), start=1):
            key = self.storage.save_evidence_frame(
                self.camera_id, item.incident_id, f"after_{ordinal}", item.frames[index]
            )
            evidence["frames"].append(
                {
                    "label": f"{self._relative_seconds(index - item.event_sample_index)}s after",
                    "relative_seconds": self._relative_seconds(index - item.event_sample_index),
                    "key": key,
                }
            )

        try:
            evidence["clip"] = {
                "key": self.storage.save_evidence_clip(
                    self.camera_id, item.incident_id, item.frames, self.capture_fps
                ),
                "duration_seconds": round(len(item.frames) / self.capture_fps, 1),
            }
            evidence["status"] = "ready"
        except Exception as exc:  # still images remain valid review evidence
            evidence["status"] = "frames_ready"
            evidence["clip_error"] = str(exc)
        return evidence

    def _pre_indices(self, event_index: int) -> list[int]:
        if event_index <= 0:
            return []
        candidates = {max(0, event_index - round(self.capture_fps * 1.5)), max(0, event_index - round(self.capture_fps * 0.5))}
        return sorted(index for index in candidates if index < event_index)

    def _post_indices(self, post_start: int, post_count: int) -> list[int]:
        if post_count <= 0:
            return []
        candidates = {
            post_start + min(post_count - 1, max(0, round(self.capture_fps * 0.5) - 1)),
            post_start + post_count - 1,
        }
        return sorted(candidates)

    def _relative_seconds(self, sample_offset: int) -> float:
        return round(sample_offset / self.capture_fps, 1)
