"""
Job tracking and management for background training tasks
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TrainingJobManager:
    """Manage training jobs with persistent storage"""
    
    def __init__(self, jobs_dir: str = "training_jobs"):
        self.jobs_dir = Path(jobs_dir)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
    
    def create_job(self, video_path: str, classes: list, epochs: int) -> str:
        """Create a new training job and return job_id"""
        job_id = str(uuid.uuid4())[:8]
        
        job_data = {
            "job_id": job_id,
            "status": JobStatus.PENDING,
            "video_path": video_path,
            "classes": classes,
            "epochs": epochs,
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "progress": 0,
            "message": "Job queued",
            "results": None,
            "error": None
        }
        
        # Save job info
        job_file = self.jobs_dir / f"{job_id}.json"
        with open(job_file, "w") as f:
            json.dump(job_data, f, indent=2)
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job information"""
        job_file = self.jobs_dir / f"{job_id}.json"
        if not job_file.exists():
            return None
        
        with open(job_file, "r") as f:
            return json.load(f)
    
    def update_job(self, job_id: str, **kwargs):
        """Update job status and info"""
        job_data = self.get_job(job_id)
        if not job_data:
            raise ValueError(f"Job not found: {job_id}")
        
        # Update fields
        for key, value in kwargs.items():
            if key in job_data:
                job_data[key] = value
        
        # Save updated job
        job_file = self.jobs_dir / f"{job_id}.json"
        with open(job_file, "w") as f:
            json.dump(job_data, f, indent=2)
    
    def start_job(self, job_id: str):
        """Mark job as running"""
        self.update_job(
            job_id,
            status=JobStatus.RUNNING,
            started_at=datetime.now().isoformat(),
            message="Training started"
        )
    
    def complete_job(self, job_id: str, results: Dict):
        """Mark job as completed"""
        self.update_job(
            job_id,
            status=JobStatus.COMPLETED,
            completed_at=datetime.now().isoformat(),
            progress=100,
            message="Training completed successfully",
            results=results
        )
    
    def fail_job(self, job_id: str, error: str):
        """Mark job as failed"""
        self.update_job(
            job_id,
            status=JobStatus.FAILED,
            completed_at=datetime.now().isoformat(),
            message="Training failed",
            error=error
        )
    
    def update_progress(self, job_id: str, progress: int, message: str):
        """Update job progress"""
        self.update_job(
            job_id,
            progress=progress,
            message=message
        )


# Global job manager instance
job_manager = TrainingJobManager()
