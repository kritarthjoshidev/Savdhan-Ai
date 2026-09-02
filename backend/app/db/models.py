from sqlalchemy import Column, Integer, String, JSON, DateTime, Float, Boolean, Text
from sqlalchemy.sql import func
from app.db.base import Base

class Incident(Base):
    """Detected incident/alert model"""
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    source_cam = Column(String, index=True)  # camera ID
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    bbox = Column(JSON)  # [x, y, w, h]
    snapshot_path = Column(String)  # MinIO URL / key
    status = Column(String, default="pending", index=True)  # pending/verified/rejected
    confidence = Column(Float)  # detection confidence
    track_id = Column(String, nullable=True)  # tracking ID across frames
    meta = Column(JSON)  # extra info (similarity, embeddings, etc.)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Model(Base):
    """Trained model registry"""
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, index=True)
    version = Column(String)
    base_model = Column(String)  # yolov8n, yolov8s, etc.
    artifact_path = Column(String)  # MLflow artifact path or MinIO path
    mlflow_run_id = Column(String, nullable=True)
    mlflow_experiment_id = Column(String, nullable=True)
    metrics = Column(JSON)  # mAP, precision, recall, etc.
    status = Column(String, default="candidate")  # candidate/production/archived
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class TrainJob(Base):
    """Training job record"""
    __tablename__ = "train_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Configuration
    config = Column(JSON)  # {data_yaml, epochs, batch_size, model, etc.}
    status = Column(String, default="queued", index=True)  # queued/running/done/failed
    
    # Celery task info
    celery_task_id = Column(String, nullable=True)
    
    # Results
    result = Column(JSON)  # {model_path, metrics, error, etc.}
    logs = Column(Text, nullable=True)  # training logs
    
class Snapshot(Base):
    """Saved frames/snapshots from incidents"""
    __tablename__ = "snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer)  # reference to incident
    minio_key = Column(String, index=True)
    embedding = Column(JSON)  # Re-ID embedding vector
    created_at = Column(DateTime(timezone=True), server_default=func.now())
