import logging
import cv2
import numpy as np
from collections import Counter
from typing import Optional
from app.ml.yolo_infer import YOLOInference
from app.ml.border_analytics import CameraFences
from app.ml.motion_gate import MotionGate
from app.ml.reid_embed import ReIDEmbedding
from app.db.database import SessionLocal
from app.db import crud
from app.db.models import Snapshot
from app.services.storage import get_storage
from app.core.events import publish_alert
import asyncio

logger = logging.getLogger(__name__)

class DetectionWorker:
    """Worker that processes video frames and runs YOLO detection"""
    
    def __init__(self, model_path: str = "yolov8s-world.pt", fence_y_ratio: float = 0.50):
        """Initialize detection worker"""
        self.yolo = YOLOInference(model_path)
        self.storage = get_storage()
        self.db = SessionLocal()
        self.virtual_fences = CameraFences(fence_y_ratio=fence_y_ratio)
        self.motion_gate = MotionGate()
        self.reid = ReIDEmbedding()
        
    def process_video_stream(
        self,
        video_source: str,
        cam_id: str,
        conf_threshold: float = 0.35,
        sample_every_n_frames: int = 5,
    ):
        """
        Process video stream from file or RTSP
        
        Args:
            video_source: Video file path or RTSP URL
            cam_id: Camera identifier
            conf_threshold: Confidence threshold for detections
            sample_every_n_frames: Run model inference once per N video frames.
        """
        try:
            cap = cv2.VideoCapture(video_source)
            if not cap.isOpened():
                logger.error(f"Failed to open video source: {video_source}")
                return
            
            frame_count = 0
            motion_frames = 0
            analyzed_frames = 0
            intrusion_count = 0
            total_detections = 0
            person_detections = 0
            class_counts = Counter()
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # The motion gate prevents costly model calls on static frames;
                # configurable sampling makes CPU-only offline demos practical.
                if frame_count % sample_every_n_frames == 0:
                    enhanced_frame = self.yolo.enhance_low_light(frame)
                    motion = self.motion_gate.update(enhanced_frame)
                    if not motion.active:
                        continue
                    motion_frames += 1
                    detections = self.yolo.process_frame(enhanced_frame, conf_threshold)
                    analyzed_frames += 1
                    total_detections += len(detections)
                    class_counts.update(item["class_name"] for item in detections)
                    
                    for detection in detections:
                        # A virtual fence is an actual border boundary: only a
                        # person crossing from the safe side triggers intrusion.
                        if detection["class_name"] != "person":
                            continue
                        person_detections += 1
                        border_state = self.virtual_fences.update(
                            cam_id, detection["bbox"], frame.shape[0]
                        )
                        if border_state["intrusion"]:
                            self._handle_detection(
                                enhanced_frame, cam_id, detection, frame_count, border_state
                            )
                            intrusion_count += 1
            
            cap.release()
            logger.info(f"Finished processing video from {cam_id}")
            return {
                "frames_read": frame_count,
                "motion_frames": motion_frames,
                "frames_analyzed": analyzed_frames,
                "total_detections": total_detections,
                "person_detections": person_detections,
                "class_counts": dict(class_counts),
                "intrusions": intrusion_count,
            }
            
        except Exception as e:
            logger.error(f"Error processing video stream: {e}")
        finally:
            self.db.close()

    def _handle_detection(
        self,
        frame: np.ndarray,
        cam_id: str,
        detection: dict,
        frame_id: int,
        border_state: dict,
    ):
        """Handle a single detection"""
        try:
            bbox = detection["bbox"]
            confidence = detection["confidence"]
            person_crop = self.yolo.crop_detection(frame, bbox)
            embedding = self.reid.get_embedding(person_crop)
            reid_match = self._find_reid_match(embedding)
            
            # Save snapshot
            snapshot_key = self.storage.save_snapshot(
                cam_id,
                frame,
                bbox,
                timestamp=f"frame_{frame_id}"
            )
            
            # Create incident record
            incident = crud.create_incident(
                self.db,
                source_cam=cam_id,
                bbox=bbox,
                snapshot_path=snapshot_key,
                confidence=confidence,
                track_id=border_state["track_id"],
                meta={
                    "detection": detection,
                    "frame_id": frame_id,
                    "event_type": "INTRUSION",
                    "virtual_fence": border_state,
                    "low_light_enhancement": "CLAHE",
                    "reid": {
                        "backend": self.reid.backend,
                        "matched_incident_id": reid_match["incident_id"] if reid_match else None,
                        "similarity": reid_match["similarity"] if reid_match else None,
                    },
                }
            )
            crud.create_snapshot(
                self.db,
                incident_id=incident.id,
                minio_key=snapshot_key,
                embedding=embedding.tolist(),
            )
            
            logger.info(f"Created incident {incident.id} from {cam_id}")
            
            # Publish alert (async)
            alert_data = {
                "event": "INTRUSION",
                "incident_id": incident.id,
                "source_cam": cam_id,
                "confidence": confidence,
                "snapshot_path": snapshot_key,
                "track_id": border_state["track_id"],
                "fence_y": border_state["fence_y"],
            }
            # Use asyncio to run async function
            asyncio.run(publish_alert("incidents", alert_data))
            
        except Exception as e:
            logger.error(f"Failed to handle detection: {e}")

    def _find_reid_match(self, embedding: np.ndarray, threshold: float = 0.70) -> Optional[dict]:
        """Compare an intrusion crop with previously recorded person snapshots."""
        snapshots = (
            self.db.query(Snapshot)
            .filter(Snapshot.embedding.is_not(None))
            .order_by(Snapshot.created_at.desc())
            .limit(200)
            .all()
        )
        gallery = [np.asarray(item.embedding, dtype=np.float32) for item in snapshots]
        match_index = self.reid.match_embedding(embedding, gallery, threshold)
        if match_index is None:
            return None
        matched = snapshots[match_index]
        return {
            "incident_id": matched.incident_id,
            "similarity": round(
                self.reid.compute_similarity(embedding, gallery[match_index]), 4
            ),
        }

# Worker instance
_detection_worker: Optional[DetectionWorker] = None

def get_detection_worker(model_path: str = "yolov8s-world.pt") -> DetectionWorker:
    """Get or create detection worker"""
    global _detection_worker
    if _detection_worker is None:
        _detection_worker = DetectionWorker(model_path)
    return _detection_worker
