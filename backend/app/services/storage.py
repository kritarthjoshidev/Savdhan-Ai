import boto3
import io
import logging
from pathlib import Path
from typing import Optional, Tuple
import cv2
import numpy as np
from app.core.config import settings

logger = logging.getLogger(__name__)


class LocalStorage:
    """Filesystem storage for a laptop demo when MinIO is not running."""

    def __init__(self):
        self.root = Path(settings.LOCAL_STORAGE_DIR)
        if not self.root.is_absolute():
            self.root = Path(__file__).resolve().parents[2] / self.root
        self.root.mkdir(parents=True, exist_ok=True)

    def save_snapshot(self, cam_id, frame, bbox=None, timestamp=None) -> str:
        if bbox:
            frame = MinIOStorage._crop_frame(frame, bbox)
        if frame.size == 0:
            raise ValueError("Cannot save an empty snapshot")
        snapshot_name = f"{timestamp or 'snapshot'}.jpg"
        key = Path("snapshots") / cam_id / snapshot_name
        destination = self.root / key
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not cv2.imwrite(str(destination), frame):
            raise RuntimeError("Failed to save snapshot locally")
        return key.as_posix()

    def save_video_chunk(self, cam_id, video_data: bytes, chunk_id: str) -> str:
        key = Path("videos") / cam_id / f"{chunk_id}.mp4"
        destination = self.root / key
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(video_data)
        return key.as_posix()

    def save_artifact(self, data: bytes, key: str) -> str:
        destination = self.root / key
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        return key

    def get_object_url(self, key: str) -> str:
        return str((self.root / key).resolve())

    def delete_object(self, key: str) -> bool:
        destination = self.root / key
        if destination.exists():
            destination.unlink()
            return True
        return False

class MinIOStorage:
    """MinIO S3-compatible object storage client"""
    
    def __init__(self):
        """Initialize MinIO client"""
        self.client = boto3.client(
            's3',
            endpoint_url=settings.MINIO_URL,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            region_name='us-east-1'
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            self.client.head_bucket(Bucket=self.bucket)
            logger.info(f"Bucket '{self.bucket}' exists")
        except:
            try:
                self.client.create_bucket(Bucket=self.bucket)
                logger.info(f"Created bucket '{self.bucket}'")
            except Exception as e:
                logger.error(f"Failed to create bucket: {e}")

    def save_snapshot(
        self,
        cam_id: str,
        frame: np.ndarray,
        bbox: Optional[list] = None,
        timestamp: Optional[str] = None
    ) -> str:
        """
        Save frame/snapshot to MinIO
        
        Args:
            cam_id: Camera ID
            frame: Frame as numpy array (BGR)
            bbox: Optional bounding box to crop
            timestamp: Optional timestamp for filename
            
        Returns:
            S3 key (path) of saved file
        """
        try:
            # Crop if bbox provided
            if bbox:
                frame = self._crop_frame(frame, bbox)
            
            # Encode frame as JPEG
            success, buffer = cv2.imencode('.jpg', frame)
            if not success:
                raise Exception("Failed to encode frame")
            
            # Create S3 key
            if timestamp:
                key = f"snapshots/{cam_id}/{timestamp}.jpg"
            else:
                import time
                key = f"snapshots/{cam_id}/{int(time.time())}.jpg"
            
            # Upload to MinIO
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=io.BytesIO(buffer),
                ContentType='image/jpeg'
            )
            
            logger.info(f"Saved snapshot to {key}")
            return key
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
            raise

    def save_video_chunk(
        self,
        cam_id: str,
        video_data: bytes,
        chunk_id: str
    ) -> str:
        """
        Save video chunk to MinIO
        
        Args:
            cam_id: Camera ID
            video_data: Video chunk as bytes
            chunk_id: Chunk identifier
            
        Returns:
            S3 key
        """
        try:
            key = f"videos/{cam_id}/{chunk_id}.mp4"
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=io.BytesIO(video_data),
                ContentType='video/mp4'
            )
            logger.info(f"Saved video chunk to {key}")
            return key
        except Exception as e:
            logger.error(f"Failed to save video: {e}")
            raise

    def save_artifact(self, data: bytes, key: str) -> str:
        """
        Save artifact (model weights, etc.) to MinIO
        
        Args:
            data: File data as bytes
            key: S3 key path
            
        Returns:
            S3 key
        """
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=io.BytesIO(data),
                ContentType='application/octet-stream'
            )
            logger.info(f"Saved artifact to {key}")
            return key
        except Exception as e:
            logger.error(f"Failed to save artifact: {e}")
            raise

    def get_object_url(self, key: str) -> str:
        """Get presigned URL for object"""
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': key},
                ExpiresIn=3600  # 1 hour
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate URL: {e}")
            return f"{settings.MINIO_URL}/{self.bucket}/{key}"

    def delete_object(self, key: str) -> bool:
        """Delete object from MinIO"""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"Deleted {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete object: {e}")
            return False

    @staticmethod
    def _crop_frame(frame: np.ndarray, bbox: list) -> np.ndarray:
        """Crop frame using bbox"""
        x_center, y_center, width, height = bbox
        x1 = int(x_center - width / 2)
        y1 = int(y_center - height / 2)
        x2 = int(x_center + width / 2)
        y2 = int(y_center + height / 2)
        
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(frame.shape[1], x2)
        y2 = min(frame.shape[0], y2)
        
        return frame[y1:y2, x1:x2]

# Singleton instance
_storage_instance: Optional[MinIOStorage | LocalStorage] = None

def get_storage() -> MinIOStorage | LocalStorage:
    """Get or create storage instance"""
    global _storage_instance
    if _storage_instance is None:
        if settings.STORAGE_BACKEND.lower() == "minio":
            _storage_instance = MinIOStorage()
        else:
            _storage_instance = LocalStorage()
    return _storage_instance
