"""Small, dependency-free virtual-fence utility used by detection workers."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import hypot
from typing import Dict, Iterable, Optional, Tuple


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
    _tracks: Dict[str, Point] = field(default_factory=dict)
    _alerted_tracks: set[str] = field(default_factory=set)
    _next_track_id: int = 1

    def _match_track(self, centroid: Point) -> str:
        nearest_id = None
        nearest_distance = self.match_distance
        for track_id, previous in self._tracks.items():
            distance = hypot(centroid[0] - previous[0], centroid[1] - previous[1])
            if distance < nearest_distance:
                nearest_id, nearest_distance = track_id, distance
        if nearest_id is not None:
            return nearest_id
        track_id = f"centroid-{self._next_track_id}"
        self._next_track_id += 1
        return track_id

    def update(
        self,
        bbox: Iterable[float],
        frame_height: int,
        track_hint: Optional[str] = None,
    ) -> dict:
        """Return track/fence state for a YOLO ``[cx, cy, w, h]`` box."""
        cx, cy, _, _ = bbox
        centroid = (float(cx), float(cy))
        track_id = track_hint or self._match_track(centroid)
        previous = self._tracks.get(track_id)
        fence_y = frame_height * self.fence_y_ratio
        crossed = (
            previous is not None
            and previous[1] < fence_y <= centroid[1]
        )
        direction = None
        if previous is not None and previous[1] != centroid[1]:
            direction = "above_to_below" if centroid[1] > previous[1] else "below_to_above"
        # A physical crossing should create one alert for this track, not one
        # alert for every noisy position update after the line.
        intrusion = crossed and track_id not in self._alerted_tracks
        if intrusion:
            self._alerted_tracks.add(track_id)
        self._tracks[track_id] = centroid
        return {
            "track_id": track_id,
            "fence_y": round(fence_y, 2),
            "centroid": [round(cx, 2), round(cy, 2)],
            "intrusion": intrusion,
            "direction": direction,
        }


@dataclass
class CameraFences:
    """Keep tripwire tracking state isolated for each camera feed."""

    fence_y_ratio: float = 0.50
    match_distance: float = 100.0
    _fences: Dict[str, VirtualFence] = field(default_factory=dict)

    def update(
        self,
        camera_id: str,
        bbox: Iterable[float],
        frame_height: int,
        track_hint: Optional[str] = None,
    ) -> dict:
        fence = self._fences.setdefault(
            camera_id,
            VirtualFence(
                fence_y_ratio=self.fence_y_ratio,
                match_distance=self.match_distance,
            ),
        )
        return fence.update(bbox, frame_height, track_hint=track_hint)
