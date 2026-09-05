"""Camera setup endpoints used by the command-centre UI."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.camera_manager import get_camera_manager

router = APIRouter(prefix="/cameras", tags=["cameras"])


class CameraCreate(BaseModel):
    camera_id: str = Field(..., min_length=1, max_length=80)
    name: str = Field("", max_length=100)
    stream_url: str = Field(..., min_length=8, max_length=1000)


class CameraTest(BaseModel):
    stream_url: str = Field(..., min_length=8, max_length=1000)


class CameraStart(BaseModel):
    analysis_mode: str = Field("auto", pattern="^(border|traffic|auto)$")
    confidence_threshold: float = Field(0.35, ge=0.05, le=0.95)
    sample_every_n_frames: int = Field(8, ge=1, le=120)
    fence_y_ratio: float = Field(0.5, gt=0.05, lt=0.95)
    accident_threshold: float = Field(0.52, ge=0.35, le=0.90)


def _http_error(error: Exception) -> HTTPException:
    if isinstance(error, KeyError):
        return HTTPException(status_code=404, detail="Camera not found")
    return HTTPException(status_code=422, detail=str(error))


@router.get("/")
def list_cameras():
    return get_camera_manager().list()


@router.post("/test")
def test_camera(request: CameraTest):
    try:
        return get_camera_manager().test(request.stream_url)
    except Exception as exc:
        raise _http_error(exc) from exc


@router.post("/", status_code=201)
def add_camera(request: CameraCreate):
    try:
        return get_camera_manager().add(request.camera_id, request.name, request.stream_url)
    except Exception as exc:
        raise _http_error(exc) from exc


@router.post("/{camera_id}/start")
def start_camera(camera_id: str, request: CameraStart):
    try:
        return get_camera_manager().start(camera_id, **request.model_dump())
    except Exception as exc:
        raise _http_error(exc) from exc


@router.post("/{camera_id}/stop")
def stop_camera(camera_id: str):
    try:
        return get_camera_manager().stop(camera_id)
    except Exception as exc:
        raise _http_error(exc) from exc


@router.delete("/{camera_id}", status_code=204)
def delete_camera(camera_id: str):
    try:
        get_camera_manager().delete(camera_id)
    except Exception as exc:
        raise _http_error(exc) from exc
