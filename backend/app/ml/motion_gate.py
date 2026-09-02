"""Motion gate adapted from the useful MOG2/ROI idea in the cloned CCTV repo.

It deliberately contains no Telegram, camera credentials, or side effects.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class MotionResult:
    active: bool
    largest_contour_area: float


class MotionGate:
    """Skip expensive model inference when a frame contains no sustained motion."""

    def __init__(
        self,
        min_contour_area: float = 900.0,
        persistence_frames: int = 2,
        warmup_frames: int = 10,
    ) -> None:
        self.background = cv2.createBackgroundSubtractorMOG2(
            history=200, varThreshold=24, detectShadows=False
        )
        self.min_contour_area = min_contour_area
        self.persistence_frames = persistence_frames
        self.warmup_frames = warmup_frames
        self._frames_seen = 0
        self._active_streak = 0

    def update(self, frame: np.ndarray) -> MotionResult:
        """Return whether movement is persistent enough to warrant inference."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mask = self.background.apply(gray)
        mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)[1]
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        mask = cv2.dilate(mask, None, iterations=2)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        largest_area = max((cv2.contourArea(contour) for contour in contours), default=0.0)

        self._frames_seen += 1
        if self._frames_seen <= self.warmup_frames:
            return MotionResult(active=False, largest_contour_area=largest_area)

        self._active_streak = (
            self._active_streak + 1 if largest_area >= self.min_contour_area else 0
        )
        return MotionResult(
            active=self._active_streak >= self.persistence_frames,
            largest_contour_area=largest_area,
        )
