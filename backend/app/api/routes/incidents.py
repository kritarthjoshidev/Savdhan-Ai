from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.db.database import get_db
from app.db import crud
from app.core.events import publish_alert
from app.services.storage import LocalStorage, get_storage
from urllib.parse import quote
import json

router = APIRouter()


def _media_reference(request: Request, key: Optional[str], label: Optional[str] = None) -> Optional[dict]:
    """Turn an internal storage key into a browser-safe evidence reference."""
    if not key:
        return None
    if key.startswith(("http://", "https://")):
        return {"key": key, "url": key, "label": label, "available": True}
    storage = get_storage()
    if isinstance(storage, LocalStorage):
        try:
            available = storage.get_local_path(key).is_file()
        except ValueError:
            available = False
        base = str(request.base_url).rstrip("/")
        return {
            "key": key,
            "url": f"{base}/api/v1/media/{quote(key, safe='/')}" if available else None,
            "label": label,
            "available": available,
        }
    return {
        "key": key,
        "url": storage.get_object_url(key),
        "label": label,
        "available": True,
    }

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


@router.get("/{incident_id}/evidence")
def get_incident_evidence(
    incident_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Return playable URLs for the trigger image, context frames, and clip.

    The database stores only object keys. This endpoint deliberately resolves
    them to URLs so an operator never has to copy a local file path manually.
    """
    incident = crud.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    evidence = (incident.meta or {}).get("evidence") or {}
    clip = evidence.get("clip") or {}
    frames = [
        _media_reference(request, item.get("key"), item.get("label"))
        for item in evidence.get("frames", [])
    ]
    return {
        "incident_id": incident.id,
        "status": evidence.get("status", "not_available"),
        "snapshot": _media_reference(request, incident.snapshot_path, "Person crop"),
        "detected_frame": _media_reference(
            request,
            (evidence.get("detected_frame") or {}).get("key"),
            (evidence.get("detected_frame") or {}).get("label", "Detection frame"),
        ),
        "frames": [frame for frame in frames if frame],
        "clip": _media_reference(request, clip.get("key"), "Context clip"),
        "clip_duration_seconds": clip.get("duration_seconds"),
        "event_frame_id": evidence.get("event_frame_id"),
        "capture_fps": evidence.get("capture_fps"),
    }
