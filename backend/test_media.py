import numpy as np
from fastapi.testclient import TestClient

from app.api.main import app
import app.services.storage as storage_module
from app.services.storage import LocalStorage


def test_local_evidence_media_is_browser_accessible(tmp_path):
    local_storage = LocalStorage()
    local_storage.root = tmp_path
    old_storage = storage_module._storage_instance
    storage_module._storage_instance = local_storage
    try:
        key = local_storage.save_evidence_frame(
            "test-camera", 11, "detected", np.zeros((20, 20, 3), dtype=np.uint8)
        )
        response = TestClient(app).get(f"/api/v1/media/{key}")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/jpeg")
        assert response.content
    finally:
        storage_module._storage_instance = old_storage


def test_registered_camera_websocket_returns_a_clear_error_for_unknown_camera():
    with TestClient(app).websocket_connect("/api/v1/live/camera/stream?camera_id=missing") as websocket:
        message = websocket.receive_json()
    assert message == {"type": "error", "error": "Camera not found"}
