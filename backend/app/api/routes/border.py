"""API entry points for the SIH border-intrusion processing pipeline."""

from pathlib import Path
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field

from app.workers.detection_worker import DetectionWorker


router = APIRouter(prefix="/border", tags=["border-surveillance"])


class BorderProcessingRequest(BaseModel):
    """Start virtual-fence analysis on a local recording or an RTSP camera."""

    source: str = Field(..., description="Local video path or RTSP URL")
    source_type: Literal["file", "rtsp"] = "file"
    camera_id: str = Field(..., min_length=1, max_length=100)
    confidence_threshold: float = Field(0.35, ge=0.05, le=0.95)
    sample_every_n_frames: int = Field(
        30,
        ge=1,
        le=300,
        description="Inference interval; 30 is about one frame per second for a 30 FPS file.",
    )
    fence_y_ratio: float = Field(
        0.50,
        gt=0.05,
        lt=0.95,
        description="Horizontal virtual-fence position as a fraction of frame height.",
    )


def run_border_processing(request: BorderProcessingRequest) -> None:
    """Run outside the request handler so API clients receive an immediate ACK."""
    worker = DetectionWorker(fence_y_ratio=request.fence_y_ratio)
    worker.process_video_stream(
        video_source=request.source,
        cam_id=request.camera_id,
        conf_threshold=request.confidence_threshold,
        sample_every_n_frames=request.sample_every_n_frames,
    )


@router.post("/process", status_code=status.HTTP_202_ACCEPTED)
async def process_border_source(
    request: BorderProcessingRequest,
    background_tasks: BackgroundTasks,
):
    """Queue a YOLO-World + CLAHE + tripwire detection run.

    Only crossings by a ``person`` from above to below the configured virtual
    fence create an ``INTRUSION`` incident and a real-time WebSocket alert.
    """
    if request.source_type == "file" and not Path(request.source).is_file():
        raise HTTPException(status_code=404, detail="Video file was not found")
    if request.source_type == "rtsp" and not request.source.startswith("rtsp://"):
        raise HTTPException(status_code=422, detail="RTSP source must begin with rtsp://")

    background_tasks.add_task(run_border_processing, request)
    return {
        "status": "accepted",
        "camera_id": request.camera_id,
        "event_on_crossing": "INTRUSION",
        "fence_y_ratio": request.fence_y_ratio,
        "sample_every_n_frames": request.sample_every_n_frames,
    }
