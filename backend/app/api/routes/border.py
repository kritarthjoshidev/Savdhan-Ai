"""API entry points for the SIH border-intrusion processing pipeline."""

from pathlib import Path
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field

from app.workers.detection_worker import DetectionWorker


router = APIRouter(prefix="/border", tags=["border-surveillance"])


class BorderProcessingRequest(BaseModel):
    """Start border, traffic, or automatic incident analysis."""

    source: str = Field(..., description="Local video path or RTSP/HTTP camera URL")
    source_type: Literal["file", "rtsp", "stream"] = "file"
    camera_id: str = Field(..., min_length=1, max_length=100)
    analysis_mode: Literal["border", "traffic", "auto"] = Field(
        "auto",
        description="border = tripwire intrusion; traffic = crash scene; auto = choose from CLIP scene context.",
    )
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
    accident_threshold: float = Field(
        0.52,
        ge=0.35,
        le=0.90,
        description="Minimum CLIP accident score in traffic/auto mode.",
    )


def run_border_processing(request: BorderProcessingRequest) -> None:
    """Run outside the request handler so API clients receive an immediate ACK."""
    worker = DetectionWorker(
        fence_y_ratio=request.fence_y_ratio,
        analysis_mode=request.analysis_mode,
        accident_threshold=request.accident_threshold,
    )
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
    """Queue domain-aware border or traffic incident analysis.

    Border mode creates ``BORDER_INTRUSION`` only after one tracked person
    crosses the virtual fence. Traffic mode creates ``TRAFFIC_ACCIDENT`` only
    after consecutive CLIP crash-scene confirmations. Auto selects a profile
    from the source's scene context.
    """
    if request.source_type == "file" and not Path(request.source).is_file():
        raise HTTPException(status_code=404, detail="Video file was not found")
    if request.source_type in {"rtsp", "stream"} and not request.source.startswith(("rtsp://", "http://", "https://")):
        raise HTTPException(
            status_code=422,
            detail="Camera source must begin with rtsp://, http://, or https://",
        )

    background_tasks.add_task(run_border_processing, request)
    return {
        "status": "accepted",
        "camera_id": request.camera_id,
        "analysis_mode": request.analysis_mode,
        "possible_events": (
            ["BORDER_INTRUSION"] if request.analysis_mode == "border"
            else ["TRAFFIC_ACCIDENT"] if request.analysis_mode == "traffic"
            else ["BORDER_INTRUSION", "TRAFFIC_ACCIDENT"]
        ),
        "fence_y_ratio": request.fence_y_ratio,
        "sample_every_n_frames": request.sample_every_n_frames,
        "accident_threshold": request.accident_threshold,
    }
