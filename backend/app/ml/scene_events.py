"""Domain-aware event classification for traffic and border surveillance."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import cv2
import numpy as np


EVENT_BORDER_INTRUSION = "BORDER_INTRUSION"
EVENT_TRAFFIC_ACCIDENT = "TRAFFIC_ACCIDENT"

_PROMPTS = [
    "a traffic accident with crashed vehicles",
    "normal road traffic",
    "a person crossing a border fence",
    "a normal border security area",
]


class SceneEventClassifier:
    """Use local CLIP zero-shot scores as a semantic second opinion.

    YOLO answers *what objects are visible*. CLIP helps answer *what is
    happening in the whole scene*, which is essential for an accident event.
    The model is loaded lazily so pure border operation stays light.
    """

    def __init__(self, model_path: Optional[str] = None):
        self._custom_model_path = model_path is not None
        self.model_path = Path(model_path) if model_path else self._default_model_path()
        self._model = None
        self._preprocess = None
        self._tokens = None
        self._torch = None
        self.available = True
        self.load_error: Optional[str] = None

    @staticmethod
    def _default_model_path() -> Path:
        return Path(__file__).resolve().parents[2] / "weights" / "clip" / "ViT-B-32.pt"

    def _ensure_loaded(self) -> bool:
        if self._model is not None:
            return True
        if not self.available:
            return False
        try:
            import clip
            import torch

            model_source = str(self.model_path)
            if not self.model_path.is_file():
                if self._custom_model_path:
                    raise FileNotFoundError(f"CLIP weights not found: {self.model_path}")
                # OpenAI CLIP downloads the 338 MB checkpoint once and caches
                # it here, making a clean demo setup self-bootstrapping.
                model_source = "ViT-B/32"
            self._model, self._preprocess = clip.load(
                model_source,
                device="cpu",
                download_root=str(self.model_path.parent),
            )
            self._model.eval()
            self._tokens = clip.tokenize(_PROMPTS)
            self._torch = torch
            return True
        except Exception as exc:
            self.available = False
            self.load_error = str(exc)
            return False

    def classify(self, frame: np.ndarray) -> dict:
        """Return calibrated traffic/border scene probabilities for one frame."""
        if not self._ensure_loaded():
            return {
                "available": False,
                "error": self.load_error or "CLIP unavailable",
                "scores": {},
                "domain": "border",
                "domain_confidence": 0.0,
            }

        from PIL import Image

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = self._preprocess(Image.fromarray(rgb)).unsqueeze(0)
        with self._torch.no_grad():
            logits, _ = self._model(image, self._tokens)
            probabilities = self._torch.softmax(logits, dim=-1)[0].tolist()

        scores = dict(zip(("traffic_accident", "normal_traffic", "border_crossing", "normal_border"), probabilities))
        traffic_context = scores["traffic_accident"] + scores["normal_traffic"]
        border_context = scores["border_crossing"] + scores["normal_border"]
        domain = "traffic" if traffic_context >= border_context else "border"
        return {
            "available": True,
            "scores": {name: round(float(value), 4) for name, value in scores.items()},
            "domain": domain,
            "domain_confidence": round(float(max(traffic_context, border_context)), 4),
        }


@dataclass
class TrafficAccidentState:
    """Require consecutive semantic confirmations and emit once per scene."""

    threshold: float = 0.52
    confirmations_required: int = 2
    positive_streak: int = 0
    negative_streak: int = 0
    active: bool = False

    def observe(self, semantic: dict) -> bool:
        scores = semantic.get("scores") or {}
        accident_score = float(scores.get("traffic_accident", 0.0))
        traffic_context = accident_score + float(scores.get("normal_traffic", 0.0))
        positive = semantic.get("domain") == "traffic" and traffic_context >= 0.65 and accident_score >= self.threshold

        if positive:
            self.positive_streak += 1
            self.negative_streak = 0
            if self.positive_streak >= self.confirmations_required and not self.active:
                self.active = True
                return True
            return False

        self.positive_streak = 0
        self.negative_streak += 1
        # Require a little normal context before a later, distinct accident can alert.
        if self.negative_streak >= self.confirmations_required:
            self.active = False
        return False


@dataclass
class IncidentDeduplicator:
    """Last line of defence against repeated alerts for the same scene/track."""

    cooldown_seconds: float = 45.0
    _last_frame: dict[tuple[str, str, str], int] = field(default_factory=dict)

    def claim(
        self, camera_id: str, event_type: str, track_id: str, frame_id: int, source_fps: float
    ) -> bool:
        key = (camera_id, event_type, track_id)
        cooldown_frames = max(1, int(max(1.0, source_fps) * self.cooldown_seconds))
        previous = self._last_frame.get(key)
        if previous is not None and frame_id - previous < cooldown_frames:
            return False
        self._last_frame[key] = frame_id
        return True
