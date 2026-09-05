import numpy as np

from app.services.evidence import EvidenceRecorder


class FakeStorage:
    def save_evidence_frame(self, camera_id, incident_id, label, frame):
        assert frame.size
        return f"evidence/{camera_id}/{incident_id}/{label}.jpg"

    def save_evidence_clip(self, camera_id, incident_id, frames, fps):
        assert frames
        assert fps > 0
        return f"evidence/{camera_id}/{incident_id}/context.mp4"


def test_evidence_recorder_exposes_frame_then_short_clip():
    recorder = EvidenceRecorder(
        FakeStorage(), "phone-gate", source_fps=4, pre_seconds=1, post_seconds=1, capture_fps=4
    )
    frame = np.zeros((20, 20, 3), dtype=np.uint8)
    recorder.observe(frame, 1)

    initial = recorder.begin(7, 1, np.ones((20, 20, 3), dtype=np.uint8))
    assert initial["status"] == "recording"
    assert initial["detected_frame"]["key"].endswith("detected.jpg")

    completed = []
    for frame_id in range(2, 6):
        completed.extend(recorder.observe(frame, frame_id))

    assert len(completed) == 1
    incident_id, evidence = completed[0]
    assert incident_id == 7
    assert evidence["status"] == "ready"
    assert evidence["clip"]["key"].endswith("context.mp4")
    assert evidence["frames"]
