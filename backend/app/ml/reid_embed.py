"""Person re-identification using OSNet, based on the cloned ReID reference.

The module keeps a deterministic visual-signature fallback so the incident
pipeline remains usable if OSNet is unavailable on a future demo machine.
"""

from __future__ import annotations

import logging
from typing import List, Optional

import cv2
import numpy as np


logger = logging.getLogger(__name__)


class ReIDEmbedding:
    """Extract OSNet appearance vectors and compare them with cosine similarity."""

    def __init__(self, model_type: str = "osnet_x1_0", device: str = "cpu") -> None:
        self.model_type = model_type
        self.device = device
        self.extractor = None
        self.backend = "color-histogram-fallback"
        self.embedding_dim = 512
        try:
            import torchreid

            self.extractor = torchreid.utils.FeatureExtractor(
                model_name=model_type,
                device=device,
                verbose=False,
            )
            self.backend = "torchreid-osnet"
            logger.info("Re-ID ready with %s on %s", model_type, device)
        except Exception as error:
            logger.warning("OSNet unavailable; using deterministic fallback: %s", error)

    @staticmethod
    def _normalize(vector: np.ndarray) -> np.ndarray:
        vector = vector.astype(np.float32).reshape(-1)
        norm = float(np.linalg.norm(vector))
        return vector / norm if norm else vector

    def _fallback_embedding(self, image_bgr: np.ndarray) -> np.ndarray:
        """Stable HSV histogram fallback; never generates random identity vectors."""
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
        histogram = cv2.calcHist(
            [hsv], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256]
        )
        return self._normalize(histogram)

    def get_embedding(self, image_bgr: np.ndarray) -> np.ndarray:
        """Create a normalized appearance vector for one non-empty person crop."""
        if image_bgr is None or image_bgr.size == 0:
            raise ValueError("Cannot embed an empty person crop")
        if self.extractor is None:
            return self._fallback_embedding(image_bgr)

        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        embedding = self.extractor([image_rgb]).cpu().numpy()[0]
        return self._normalize(embedding)

    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Cosine similarity of two normalized or unnormalized vectors."""
        first = self._normalize(embedding1)
        second = self._normalize(embedding2)
        if first.size != second.size or not first.size or not second.size:
            return 0.0
        return float(np.clip(np.dot(first, second), -1.0, 1.0))

    def match_embedding(
        self,
        embedding: np.ndarray,
        gallery: List[np.ndarray],
        threshold: float = 0.70,
    ) -> Optional[int]:
        """Return the closest gallery index if its similarity passes threshold."""
        if not gallery:
            return None
        similarities = [self.compute_similarity(embedding, item) for item in gallery]
        best_index = int(np.argmax(similarities))
        return best_index if similarities[best_index] >= threshold else None
