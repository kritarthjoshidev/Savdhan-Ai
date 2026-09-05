from app.ml.border_analytics import VirtualFence
from app.ml.scene_events import IncidentDeduplicator, TrafficAccidentState
from app.workers.detection_worker import DetectionWorker


def _traffic_scene(accident_score: float) -> dict:
    return {
        "domain": "traffic",
        "scores": {
            "traffic_accident": accident_score,
            "normal_traffic": 1.0 - accident_score,
        },
    }


def test_traffic_accident_requires_two_confirmations_and_emits_once():
    state = TrafficAccidentState(threshold=0.52, confirmations_required=2)

    assert state.observe(_traffic_scene(0.66)) is False
    assert state.observe(_traffic_scene(0.66)) is True
    assert state.observe(_traffic_scene(0.66)) is False


def test_traffic_accident_rearms_only_after_normal_scene():
    state = TrafficAccidentState(threshold=0.52, confirmations_required=2)
    state.observe(_traffic_scene(0.66))
    assert state.observe(_traffic_scene(0.66)) is True

    assert state.observe(_traffic_scene(0.10)) is False
    assert state.observe(_traffic_scene(0.10)) is False
    assert state.observe(_traffic_scene(0.66)) is False
    assert state.observe(_traffic_scene(0.66)) is True


def test_tripwire_emits_once_for_a_persistent_tracked_person():
    fence = VirtualFence(fence_y_ratio=0.5)
    assert fence.update([100, 45, 20, 20], frame_height=100, track_hint="track-7")["intrusion"] is False
    assert fence.update([100, 55, 20, 20], frame_height=100, track_hint="track-7")["intrusion"] is True
    assert fence.update([100, 65, 20, 20], frame_height=100, track_hint="track-7")["intrusion"] is False


def test_deduplicator_blocks_same_track_inside_cooldown():
    deduplicator = IncidentDeduplicator(cooldown_seconds=45)
    assert deduplicator.claim("cam-1", "TRAFFIC_ACCIDENT", "scene", frame_id=100, source_fps=30)
    assert not deduplicator.claim("cam-1", "TRAFFIC_ACCIDENT", "scene", frame_id=200, source_fps=30)
    assert deduplicator.claim("cam-1", "TRAFFIC_ACCIDENT", "scene", frame_id=1450, source_fps=30)


def test_event_explanations_name_the_incident_type_and_reason():
    accident = DetectionWorker._explanation(
        "TRAFFIC_ACCIDENT",
        0.81,
        {
            "scores": {"normal_traffic": 0.08},
            "detection": {"class_name": "car"},
        },
        None,
    )
    intrusion = DetectionWorker._explanation(
        "BORDER_INTRUSION", 0.92, None, {"direction": "below_to_above"}
    )

    assert accident["finding_code"] == "TRAFFIC_ACCIDENT"
    assert "car" in accident["summary"]
    assert "crash scene" in accident["reason"]
    assert intrusion["finding_code"] == "BORDER_INTRUSION"
    assert "below to above" in intrusion["summary"]
