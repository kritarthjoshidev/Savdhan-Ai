import pytest

from app.services.camera_manager import CameraManager


def test_rejects_invalid_ipv4_octet():
    with pytest.raises(ValueError, match="Invalid camera host"):
        CameraManager.validate_url("rtsp://192.168.1.1945/")


def test_rejects_rtsp_without_stream_path():
    with pytest.raises(ValueError, match="stream path"):
        CameraManager.validate_url("rtsp://192.168.1.194:554")


def test_accepts_standard_rtsp_url():
    CameraManager.validate_url("rtsp://192.168.1.194:554/stream1")