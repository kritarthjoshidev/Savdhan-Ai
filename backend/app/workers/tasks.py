import os
from app.workers.celery_app import celery_app
from app.workers.trainer_task import train_yolo_task
import logging

logger = logging.getLogger(__name__)

# Register Celery tasks
@celery_app.task
def train_model_task(job_id: int, config: dict):
    """
    Celery task wrapper for YOLO training
    """
    return train_yolo_task(job_id, config)

@celery_app.task
def health_check():
    """
    Simple health check task
    """
    logger.info("Celery health check: OK")
    return {"status": "ok"}

if __name__ == "__main__":
    celery_app.start()
