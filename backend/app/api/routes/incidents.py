from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.db.database import get_db
from app.db import crud
from app.core.events import publish_alert
import json

router = APIRouter()

# Pydantic schemas
from pydantic import BaseModel, Field

class IncidentCreate(BaseModel):
    source_cam: str
    bbox: List[float] = Field(..., description="[x, y, w, h]")
    snapshot_path: str
    confidence: float
    track_id: Optional[str] = None
    meta: Optional[dict] = None

class IncidentUpdate(BaseModel):
    status: str  # pending/verified/rejected
    meta: Optional[dict] = None

class IncidentResponse(BaseModel):
    id: int
    source_cam: str
    timestamp: datetime
    bbox: List[float]
    snapshot_path: str
    status: str
    confidence: float
    track_id: Optional[str]
    meta: Optional[dict]
    
    class Config:
        from_attributes = True

@router.post("/", response_model=IncidentResponse)
async def create_incident(
    incident: IncidentCreate,
    db: Session = Depends(get_db)
):
    """Create a new incident/detection"""
    db_incident = crud.create_incident(
        db,
        source_cam=incident.source_cam,
        bbox=incident.bbox,
        snapshot_path=incident.snapshot_path,
        confidence=incident.confidence,
        track_id=incident.track_id,
        meta=incident.meta or {}
    )
    
    # Publish alert to Redis for real-time WebSocket notification
    await publish_alert("incidents", {
        "event": "new_incident",
        "incident_id": db_incident.id,
        "source_cam": db_incident.source_cam,
        "snapshot_path": db_incident.snapshot_path,
        "confidence": db_incident.confidence,
        "timestamp": db_incident.timestamp.isoformat()
    })
    
    return db_incident

@router.get("/", response_model=List[IncidentResponse])
def list_incidents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    status: Optional[str] = None,
    source_cam: Optional[str] = None,
    hours: int = Query(24, ge=1, le=720),
    db: Session = Depends(get_db)
):
    """List incidents with filters"""
    incidents = crud.list_incidents(
        db,
        skip=skip,
        limit=limit,
        status=status,
        source_cam=source_cam,
        hours=hours
    )
    return incidents

@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db)
):
    """Get specific incident"""
    incident = crud.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: int,
    update: IncidentUpdate,
    db: Session = Depends(get_db)
):
    """Update incident status (human verification)"""
    incident = crud.update_incident_status(
        db,
        incident_id,
        update.status,
        update.meta
    )
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Publish status update
    await publish_alert("incidents", {
        "event": "incident_updated",
        "incident_id": incident_id,
        "status": update.status
    })
    
    return incident

@router.get("/{incident_id}/snapshots")
def get_incident_snapshots(
    incident_id: int,
    db: Session = Depends(get_db)
):
    """Get all snapshots for an incident"""
    incident = crud.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    snapshots = crud.list_snapshots_for_incident(db, incident_id)
    return snapshots
