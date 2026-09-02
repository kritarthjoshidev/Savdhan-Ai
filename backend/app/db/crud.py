from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from app.db.models import Incident, TrainJob, Model, Snapshot
from datetime import datetime, timedelta

# Incident CRUD
def create_incident(db: Session, **kwargs) -> Incident:
    """Create a new incident"""
    incident = Incident(**kwargs)
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident

def get_incident(db: Session, incident_id: int) -> Optional[Incident]:
    """Get incident by ID"""
    return db.query(Incident).filter(Incident.id == incident_id).first()

def list_incidents(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    source_cam: Optional[str] = None,
    hours: int = 24
) -> List[Incident]:
    """List incidents with optional filters"""
    query = db.query(Incident)
    
    # Filter by status if provided
    if status:
        query = query.filter(Incident.status == status)
    
    # Filter by camera if provided
    if source_cam:
        query = query.filter(Incident.source_cam == source_cam)
    
    # Filter by time range (last N hours)
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    query = query.filter(Incident.timestamp >= cutoff_time)
    
    return query.order_by(desc(Incident.timestamp)).offset(skip).limit(limit).all()

def update_incident_status(
    db: Session,
    incident_id: int,
    status: str,
    meta_update: Optional[dict] = None
) -> Optional[Incident]:
    """Update incident status and metadata"""
    incident = get_incident(db, incident_id)
    if incident:
        incident.status = status
        if meta_update:
            incident.meta = {**(incident.meta or {}), **meta_update}
        db.commit()
        db.refresh(incident)
    return incident

# TrainJob CRUD
def create_train_job(db: Session, config: dict, status: str = "queued") -> TrainJob:
    """Create a new training job"""
    job = TrainJob(config=config, status=status)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

def get_train_job(db: Session, job_id: int) -> Optional[TrainJob]:
    """Get training job by ID"""
    return db.query(TrainJob).filter(TrainJob.id == job_id).first()

def update_train_job_status(
    db: Session,
    job_id: int,
    status: str,
    result: Optional[dict] = None,
    celery_task_id: Optional[str] = None
) -> Optional[TrainJob]:
    """Update training job status"""
    job = get_train_job(db, job_id)
    if job:
        job.status = status
        if status == "running":
            job.started_at = datetime.utcnow()
        elif status in ["done", "failed"]:
            job.completed_at = datetime.utcnow()
        if result:
            job.result = result
        if celery_task_id:
            job.celery_task_id = celery_task_id
        db.commit()
        db.refresh(job)
    return job

def list_train_jobs(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None
) -> List[TrainJob]:
    """List training jobs"""
    query = db.query(TrainJob)
    if status:
        query = query.filter(TrainJob.status == status)
    return query.order_by(desc(TrainJob.created_at)).offset(skip).limit(limit).all()

# Model CRUD
def create_model_record(db: Session, **kwargs) -> Model:
    """Create a new model record"""
    model = Model(**kwargs)
    db.add(model)
    db.commit()
    db.refresh(model)
    return model

def list_models(db: Session, status: Optional[str] = None) -> List[Model]:
    """List models"""
    query = db.query(Model)
    if status:
        query = query.filter(Model.status == status)
    return query.order_by(desc(Model.created_at)).all()

def get_production_model(db: Session) -> Optional[Model]:
    """Get current production model"""
    return db.query(Model).filter(Model.status == "production").first()

def set_model_production(db: Session, model_id: int) -> Optional[Model]:
    """Set a model as production (demote current if exists)"""
    # Demote current production model
    current_prod = get_production_model(db)
    if current_prod:
        current_prod.status = "archived"
    
    # Promote new model
    model = db.query(Model).filter(Model.id == model_id).first()
    if model:
        model.status = "production"
        db.commit()
        db.refresh(model)
    return model

# Snapshot CRUD
def create_snapshot(db: Session, **kwargs) -> Snapshot:
    """Create a new snapshot"""
    snapshot = Snapshot(**kwargs)
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot

def list_snapshots_for_incident(db: Session, incident_id: int) -> List[Snapshot]:
    """List snapshots for an incident"""
    return db.query(Snapshot).filter(Snapshot.incident_id == incident_id).all()
