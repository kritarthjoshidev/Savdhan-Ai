"""Small, dependency-free virtual-fence utility used by detection workers."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import hypot
from typing import Dict, Iterable, Tuple


Point = Tuple[float, float]


@dataclass
class VirtualFence:
    """Detect when a tracked object's centroid crosses a horizontal fence line.

    The lightweight nearest-centroid association is intentional: it makes the
    hackathon demo work without requiring a separate tracker service.  It can
    be replaced later by DeepSORT/ByteTrack while preserving this interface.
    """

    fence_y_ratio: float = 0.50
    match_distance: float = 100.0
    _tracks: Dict[int, Point] = field(default_factory=dict)
    _next_track_id: int = 1

    def _match_track(self, centroid: Point) -> int:
        nearest_id = None
        nearest_distance = self.match_distance
        for track_id, previous in self._tracks.items():
            distance = hypot(centroid[0] - previous[0], centroid[1] - previous[1])
            if distance < nearest_distance:
                nearest_id, nearest_distance = track_id, distance
        if nearest_id is not None:
            return nearest_id
        track_id = self._next_track_id
        self._next_track_id += 1
        return track_id

    def update(self, bbox: Iterable[float], frame_height: int) -> dict:
        """Return track/fence state for a YOLO ``[cx, cy, w, h]`` box."""
        cx, cy, _, _ = bbox
        centroid = (float(cx), float(cy))
        track_id = self._match_track(centroid)
        previous = self._tracks.get(track_id)
        fence_y = frame_height * self.fence_y_ratio
        crossed = (
            previous is not None
            and previous[1] < fence_y <= centroid[1]
        )
        self._tracks[track_id] = centroid
        return {
            "track_id": f"border-{track_id}",
            "fence_y": round(fence_y, 2),
            "centroid": [round(cx, 2), round(cy, 2)],
            "intrusion": crossed,
        }


@dataclass
class CameraFences:
    """Keep tripwire tracking state isolated for each camera feed."""

    fence_y_ratio: float = 0.50
    match_distance: float = 100.0
    _fences: Dict[str, VirtualFence] = field(default_factory=dict)

    def update(self, camera_id: str, bbox: Iterable[float], frame_height: int) -> dict:
        fence = self._fences.setdefault(
            camera_id,
            VirtualFence(
                fence_y_ratio=self.fence_y_ratio,
                match_distance=self.match_distance,
            ),
        )
        return fence.update(bbox, frame_height)
