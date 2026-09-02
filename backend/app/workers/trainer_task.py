import logging
import subprocess
import os
from pathlib import Path
from app.db.database import SessionLocal
from app.db import crud
from app.services.mlflow_client import get_mlflow
from app.services.storage import get_storage

logger = logging.getLogger(__name__)

def train_yolo_task(job_id: int, config: dict):
    """
    Training task - runs YOLO training and logs to MLflow
    
    This runs either:
    1. In background via FastAPI BackgroundTasks (dev)
    2. Via Celery (production) - just call this function from Celery task
    
    Args:
        job_id: Database training job ID
        config: Training configuration dict
    """
    db = SessionLocal()
    mlflow = get_mlflow()
    storage = get_storage()
    
    try:
        # Update job status
        job = crud.update_train_job_status(db, job_id, "running")
        logger.info(f"Starting training job {job_id}")
        
        # Start MLflow run
        mlflow.start_run(
            experiment_name="yolo_training",
            run_name=f"job_{job_id}"
        )
        
        # Log config
        mlflow.log_params(config)
        
        # Extract config
        model = config.get("base_model", "yolov8n.pt")
        epochs = config.get("epochs", 20)
        batch_size = config.get("batch_size", 16)
        data_yaml = config.get("data_yaml_path")
        
        # Prepare output directory
        output_dir = f"/tmp/yolo_runs/job_{job_id}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Run YOLO training via CLI
        cmd = [
            "yolo",
            "task=detect",
            "mode=train",
            f"model={model}",
            f"data={data_yaml}",
            f"epochs={epochs}",
            f"batch={batch_size}",
            f"project={output_dir}",
            "verbose=False"
        ]
        
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        
        if result.returncode != 0:
            raise Exception(f"Training failed: {result.stderr}")
        
        # Find trained weights
        runs_dir = Path(output_dir) / "detect"
        if runs_dir.exists():
            latest_run = sorted(runs_dir.iterdir())[-1]
            weights_path = latest_run / "weights" / "best.pt"
            
            if weights_path.exists():
                # Log artifact to MLflow
                mlflow.log_artifact(str(weights_path), "weights")
                
                # Upload to MinIO
                with open(weights_path, 'rb') as f:
                    storage.save_artifact(
                        f.read(),
                        f"models/yolo/{job_id}/best.pt"
                    )
                
                # Parse metrics if available (simple example)
                metrics = {
                    "training_complete": 1,
                    "epochs_completed": epochs
                }
                mlflow.log_metrics(metrics)
                
                # Update job with result
                result_data = {
                    "status": "success",
                    "weights_path": str(weights_path),
                    "metrics": metrics
                }
                crud.update_train_job_status(
                    db, job_id, "done",
                    result=result_data
                )
                logger.info(f"Training job {job_id} completed successfully")
            else:
                raise Exception("Weights file not found after training")
        else:
            raise Exception("No runs directory found")
        
        mlflow.end_run("FINISHED")
        
    except Exception as e:
        logger.error(f"Training job {job_id} failed: {e}")
        crud.update_train_job_status(
            db, job_id, "failed",
            result={"error": str(e)}
        )
        mlflow.end_run("FAILED")
    finally:
        db.close()
