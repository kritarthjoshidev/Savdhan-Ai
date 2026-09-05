"""Serve local evidence stored by the laptop-demo storage backend."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services.storage import LocalStorage, get_storage

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/{storage_key:path}")
def get_local_media(storage_key: str):
    storage = get_storage()
    if not isinstance(storage, LocalStorage):
        raise HTTPException(status_code=404, detail="Local media serving is disabled")
    try:
        path = storage.get_local_path(storage_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Evidence file was not found")
    return FileResponse(path)
