from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import threading
import os
from app.db.database import get_db
from app.db import crud
from app.workers.trainer_task import train_yolo_task
from app.services.job_manager import job_manager

# Lazy import - AutoTrainPipeline only loaded when needed
AutoTrainPipeline = None

router = APIRouter()

# Pydantic schemas
class ModelRecord(BaseModel):
    id: int
    model_name: str
    version: str
    base_model: str
    status: str
    metrics: Optional[dict]
    created_at: datetime
    
    class Config:
        from_attributes = True

class TrainJobRequest(BaseModel):
    model_name: str
    base_model: str = "yolov8n"  # yolov8n, yolov8s, yolov8m, etc.
    epochs: int = 20
    batch_size: int = 16
    data_yaml_path: str  # path to dataset YAML

class TrainJobResponse(BaseModel):
    id: int
    status: str
    config: dict
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[dict]
    
    class Config:
        from_attributes = True

class DeployModelRequest(BaseModel):
    model_id: int

class AutoTrainRequest(BaseModel):
    """Request body for auto-training endpoint"""
    video_path: str  # Path to video file (can be uploaded or use existing path)
    classes: List[str] = ["person", "motorcycle", "weapon", "helmet"]
    epochs: int = 15
    frame_interval: int = 4

class AutoTrainResponse(BaseModel):
    """Response for auto-training endpoint"""
    job_id: str
    status: str
    message: str
    created_at: str

class JobStatusResponse(BaseModel):
    """Job status response"""
    job_id: str
    status: str
    progress: int
    message: str
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    results: Optional[dict]
    error: Optional[str]

@router.get("/", response_model=List[ModelRecord])
def list_models(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all trained models"""
    models = crud.list_models(db, status=status)
    return models

@router.get("/production", response_model=Optional[ModelRecord])
def get_production_model(db: Session = Depends(get_db)):
    """Get current production model"""
    model = crud.get_production_model(db)
    if not model:
        raise HTTPException(status_code=404, detail="No production model deployed")
    return model

@router.post("/train", response_model=TrainJobResponse)
def trigger_training(
    request: TrainJobRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Trigger a new training job"""
    config = {
        "model_name": request.model_name,
        "base_model": request.base_model,
        "epochs": request.epochs,
        "batch_size": request.batch_size,
        "data_yaml_path": request.data_yaml_path
    }
    
    # Create training job record
    job = crud.create_train_job(db, config=config, status="queued")
    
    # Queue the training task (this will run asynchronously)
    # We use background_tasks for local dev; in production use Celery
    background_tasks.add_task(
        train_yolo_task,
        job_id=job.id,
        config=config
    )
    
    return job

@router.get("/train/{job_id}", response_model=TrainJobResponse)
def get_train_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Get training job status"""
    job = crud.get_train_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Training job not found")
    return job

@router.get("/train", response_model=List[TrainJobResponse])
def list_train_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all training jobs"""
    jobs = crud.list_train_jobs(db, skip=skip, limit=limit, status=status)
    return jobs

@router.post("/deploy", response_model=ModelRecord)
def deploy_model(
    request: DeployModelRequest,
    db: Session = Depends(get_db)
):
    """Deploy a model to production"""
    model = crud.set_model_production(db, request.model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model

@router.get("/train/{job_id}/logs")
def get_train_logs(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Get training logs"""
    job = crud.get_train_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Training job not found")
    return {"logs": job.logs or "No logs available yet"}


# ============================================================================
# AUTO-TRAINING ENDPOINTS (1-Click YOLO Pipeline)
# ============================================================================

def run_auto_train_background(job_id: str, video_path: str, classes: List[str], epochs: int, frame_interval: int):
    """Background task for running auto-train pipeline"""
    try:
        # Lazy import - load only when needed
        from auto_train import AutoTrainPipeline
        
        job_manager.start_job(job_id)
        
        # Initialize pipeline
        output_dir = f"auto_train_output/{job_id}"
        pipeline = AutoTrainPipeline(output_dir=output_dir)
        
        # Run full pipeline
        results = pipeline.run_full_pipeline(
            video_path=video_path,
            target_classes=classes,
            epochs=epochs,
            frame_interval=frame_interval
        )
        
        # Mark job as completed
        job_manager.complete_job(job_id, results)
        
    except Exception as e:
        job_manager.fail_job(job_id, str(e))
        print(f"Auto-train job {job_id} failed: {str(e)}")


@router.post("/auto-train", response_model=AutoTrainResponse)
async def auto_train_video(
    request: AutoTrainRequest,
    background_tasks: BackgroundTasks
):
    """
    1-Click Automated YOLO Training Pipeline
    
    - Extracts frames from video
    - Auto-labels using YOLO-World (zero-shot detection)
    - Fine-tunes YOLOv8n model
    - Runs inference on original video
    - Returns job_id for progress tracking
    
    Example:
    POST /api/v1/models/auto-train
    {
        "video_path": "/path/to/video.mp4",
        "classes": ["person", "motorcycle", "weapon"],
        "epochs": 15,
        "frame_interval": 4
    }
    """
    
    # Validate video file exists
    if not os.path.exists(request.video_path):
        raise HTTPException(status_code=400, detail=f"Video file not found: {request.video_path}")
    
    # Create job
    job_id = job_manager.create_job(
        video_path=request.video_path,
        classes=request.classes,
        epochs=request.epochs
    )
    
    # Queue background task
    background_tasks.add_task(
        run_auto_train_background,
        job_id=job_id,
        video_path=request.video_path,
        classes=request.classes,
        epochs=request.epochs,
        frame_interval=request.frame_interval
    )
    
    return AutoTrainResponse(
        job_id=job_id,
        status="queued",
        message="Training job submitted. Use job_id to check status.",
        created_at=datetime.now().isoformat()
    )


@router.get("/auto-train/status/{job_id}", response_model=JobStatusResponse)
async def get_auto_train_status(job_id: str):
    """
    Get status of auto-training job
    
    Example:
    GET /api/v1/models/auto-train/status/abc12345
    
    Response:
    {
        "job_id": "abc12345",
        "status": "running",
        "progress": 45,
        "message": "Training model...",
        "results": null
    }
    """
    
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        created_at=job["created_at"],
        started_at=job.get("started_at"),
        completed_at=job.get("completed_at"),
        results=job.get("results"),
        error=job.get("error")
    )


@router.get("/auto-train/download/{job_id}")
async def download_trained_model(job_id: str):
    """Download trained model weights and output video"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job not completed yet. Status: {job['status']}")
    
    results = job.get("results", {})
    
    return {
        "job_id": job_id,
        "status": "completed",
        "model_path": results.get("model_path"),
        "output_video": results.get("output_video"),
        "dataset_path": results.get("dataset_path"),
        "frames_extracted": results.get("frames_extracted"),
        "detections_count": results.get("detections_count")
    }
