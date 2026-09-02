import logging
import numpy as np
from typing import Dict, List, Optional
from app.ml.reid_embed import ReIDEmbedding
from app.db.database import SessionLocal
from app.db import crud

logger = logging.getLogger(__name__)

class TrackerWorker:
    """Worker for multi-object tracking and Re-ID matching"""
    
    def __init__(self):
        """Initialize tracker"""
        self.reid = ReIDEmbedding()
        self.db = SessionLocal()
        
        # In-memory gallery per camera
        # Structure: {cam_id: {track_id: [embeddings]}}
        self.galleries = {}
        self.max_gallery_size = 100
        
    def update_gallery(
        self,
        cam_id: str,
        track_id: str,
        embedding: np.ndarray,
        incident_id: int
    ):
        """
        Update gallery with new embedding
        
        Args:
            cam_id: Camera ID
            track_id: Track ID
            embedding: Re-ID embedding vector
            incident_id: Associated incident ID
        """
        if cam_id not in self.galleries:
            self.galleries[cam_id] = {}
        
        if track_id not in self.galleries[cam_id]:
            self.galleries[cam_id][track_id] = []
        
        # Add to gallery (keep last N embeddings)
        self.galleries[cam_id][track_id].append(embedding)
        if len(self.galleries[cam_id][track_id]) > self.max_gallery_size:
            self.galleries[cam_id][track_id].pop(0)
        
        # Save to database
        crud.create_snapshot(
            self.db,
            incident_id=incident_id,
            minio_key=f"embeddings/{cam_id}/{track_id}",
            embedding=embedding.tolist()
        )
        
        logger.info(f"Updated gallery for {cam_id}/{track_id}")

    def find_match(
        self,
        query_embedding: np.ndarray,
        cam_id: str,
        threshold: float = 0.6
    ) -> Optional[str]:
        """
        Find matching track ID in gallery
        
        Args:
            query_embedding: Query embedding
            cam_id: Camera ID to search in
            threshold: Similarity threshold
            
        Returns:
            Matching track ID or None
        """
        if cam_id not in self.galleries:
            return None
        
        best_track_id = None
        best_similarity = 0
        
        for track_id, embeddings in self.galleries[cam_id].items():
            if not embeddings:
                continue
            
            # Use most recent embedding
            recent_embedding = embeddings[-1]
            similarity = self.reid.compute_similarity(
                query_embedding,
                recent_embedding
            )
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_track_id = track_id
        
        if best_similarity >= threshold:
            logger.info(f"Found match: {best_track_id} with score {best_similarity}")
            return best_track_id
        
        return None

    def cross_camera_match(
        self,
        query_embedding: np.ndarray,
        exclude_cam: str,
        threshold: float = 0.5
    ) -> Optional[Dict]:
        """
        Search for matches across all cameras
        
        Args:
            query_embedding: Query embedding
            exclude_cam: Don't search in this camera
            threshold: Similarity threshold
            
        Returns:
            {cam_id, track_id, similarity} or None
        """
        best_match = None
        best_similarity = 0
        
        for cam_id, tracks in self.galleries.items():
            if cam_id == exclude_cam:
                continue
            
            for track_id, embeddings in tracks.items():
                if not embeddings:
                    continue
                
                recent_embedding = embeddings[-1]
                similarity = self.reid.compute_similarity(
                    query_embedding,
                    recent_embedding
                )
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = {
                        "cam_id": cam_id,
                        "track_id": track_id,
                        "similarity": similarity
                    }
        
        if best_similarity >= threshold:
            logger.info(f"Found cross-camera match: {best_match}")
            return best_match
        
        return None

# Worker instance
_tracker_worker: Optional[TrackerWorker] = None

def get_tracker_worker() -> TrackerWorker:
    """Get or create tracker worker"""
    global _tracker_worker
    if _tracker_worker is None:
        _tracker_worker = TrackerWorker()
    return _tracker_worker
