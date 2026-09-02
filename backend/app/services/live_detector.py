"""
Live camera/CCTV feed detection service
Supports: Webcam (OpenCV), RTSP streams (CCTV)
"""

import cv2
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Callable
from threading import Thread, Event
from queue import Queue
from datetime import datetime
from app.ml.yolo_infer import YOLOInference

logger = logging.getLogger(__name__)


class LiveDetector:
    """Real-time detection for webcam and RTSP streams"""
    
    def __init__(self, model_path: str = "yolov8s-world.pt"):
        """
        Initialize live detector
        
        Args:
            model_path: Path to YOLO model weights
        """
        try:
            self.inference = YOLOInference(model_path)
            self.model = self.inference.model
            logger.info(f"✓ Model loaded: {model_path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None

    def infer_frame(self, frame: np.ndarray, conf_threshold: float):
        """Run CLAHE-enhanced YOLO-World inference for a live-camera frame."""
        enhanced_frame = self.inference.enhance_low_light(frame)
        return self.model(
            enhanced_frame,
            conf=conf_threshold,
            imgsz=self.inference.image_size,
            verbose=False,
        )
    
    def detect_from_webcam(
        self,
        conf_threshold: float = 0.5,
        device_id: int = 0,
        max_frames: Optional[int] = None,
        on_detection: Optional[Callable] = None,
        on_frame: Optional[Callable] = None
    ) -> Dict:
        """
        Run real-time detection on webcam
        
        Args:
            conf_threshold: Confidence threshold for detections
            device_id: Webcam device ID (0 = default)
            max_frames: Max frames to process (None = infinite)
            on_detection: Callback function for detections
            on_frame: Callback function for each annotated frame
        
        Returns:
            Dict with statistics
        """
        if not self.model:
            logger.error("Model not loaded")
            return {"error": "Model not loaded"}
        
        logger.info(f"Starting webcam detection on device {device_id}...")
        
        cap = cv2.VideoCapture(device_id)
        if not cap.isOpened():
            error_msg = f"Failed to open webcam {device_id}"
            logger.error(error_msg)
            return {"error": error_msg}
        
        # Get camera properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        logger.info(f"Webcam info: {width}x{height} @ {fps}fps")
        
        frame_count = 0
        detections_total = 0
        classes_detected = set()
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # Run inference
                results = self.infer_frame(frame, conf_threshold)
                
                # Get annotated frame
                annotated_frame = results[0].plot()
                
                # Count detections
                detections = len(results[0].boxes)
                detections_total += detections
                
                # Track classes
                for box in results[0].boxes:
                    cls_id = int(box.cls[0])
                    label = self.model.names[cls_id]
                    classes_detected.add(label)
                    conf_score = float(box.conf[0])
                    xyxy = box.xyxy[0].tolist()
                    
                    # Call detection callback if provided
                    if on_detection:
                        on_detection({
                            "frame": frame_count,
                            "class": label,
                            "confidence": round(conf_score, 3),
                            "bbox": [round(x, 2) for x in xyxy]
                        })
                
                # Call frame callback if provided
                if on_frame:
                    on_frame(annotated_frame)
                
                if frame_count % 30 == 0:
                    logger.info(f"Processed {frame_count} frames, {detections_total} total detections")
                
                if max_frames and frame_count >= max_frames:
                    break
        
        finally:
            cap.release()
        
        stats = {
            "status": "completed",
            "frames_processed": frame_count,
            "total_detections": detections_total,
            "classes_detected": list(classes_detected),
            "avg_detections_per_frame": round(detections_total / max(frame_count, 1), 2)
        }
        
        logger.info(f"Webcam detection completed: {stats}")
        return stats
    
    def detect_from_rtsp(
        self,
        rtsp_url: str,
        conf_threshold: float = 0.5,
        max_frames: Optional[int] = None,
        on_detection: Optional[Callable] = None,
        on_frame: Optional[Callable] = None,
        timeout: int = 30
    ) -> Dict:
        """
        Run real-time detection on RTSP stream (CCTV)
        
        Args:
            rtsp_url: RTSP stream URL (e.g., rtsp://username:password@ip:port/path)
            conf_threshold: Confidence threshold
            max_frames: Max frames to process
            on_detection: Callback for detections
            on_frame: Callback for frames
            timeout: Connection timeout in seconds
        
        Returns:
            Dict with statistics
        """
        if not self.model:
            logger.error("Model not loaded")
            return {"error": "Model not loaded"}
        
        logger.info(f"Connecting to RTSP stream: {rtsp_url[:30]}...")
        
        cap = cv2.VideoCapture(rtsp_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for live feed
        
        # Wait for connection
        connected = False
        for _ in range(timeout):
            ret, frame = cap.read()
            if ret:
                connected = True
                break
            cv2.waitKey(1)
        
        if not connected:
            error_msg = f"Failed to connect to RTSP stream: {rtsp_url}"
            logger.error(error_msg)
            cap.release()
            return {"error": error_msg}
        
        # Get stream properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        logger.info(f"RTSP stream connected: {width}x{height} @ {fps}fps")
        
        frame_count = 0
        detections_total = 0
        classes_detected = set()
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    logger.warning("Stream disconnected")
                    break
                
                frame_count += 1
                
                # Run inference
                results = self.infer_frame(frame, conf_threshold)
                
                # Get annotated frame
                annotated_frame = results[0].plot()
                
                # Count detections
                detections = len(results[0].boxes)
                detections_total += detections
                
                # Track classes
                for box in results[0].boxes:
                    cls_id = int(box.cls[0])
                    label = self.model.names[cls_id]
                    classes_detected.add(label)
                    conf_score = float(box.conf[0])
                    xyxy = box.xyxy[0].tolist()
                    
                    # Call detection callback if provided
                    if on_detection:
                        on_detection({
                            "frame": frame_count,
                            "class": label,
                            "confidence": round(conf_score, 3),
                            "bbox": [round(x, 2) for x in xyxy],
                            "timestamp": datetime.now().isoformat()
                        })
                
                # Call frame callback if provided
                if on_frame:
                    on_frame(annotated_frame)
                
                if frame_count % 30 == 0:
                    logger.info(f"[RTSP] Processed {frame_count} frames, {detections_total} detections")
                
                if max_frames and frame_count >= max_frames:
                    break
        
        finally:
            cap.release()
        
        stats = {
            "status": "completed",
            "rtsp_url": rtsp_url[:30] + "...",
            "frames_processed": frame_count,
            "total_detections": detections_total,
            "classes_detected": list(classes_detected),
            "avg_detections_per_frame": round(detections_total / max(frame_count, 1), 2)
        }
        
        logger.info(f"RTSP detection completed: {stats}")
        return stats
    
    def detect_from_file(
        self,
        video_path: str,
        conf_threshold: float = 0.5,
        max_frames: Optional[int] = None,
        on_detection: Optional[Callable] = None,
        on_frame: Optional[Callable] = None
    ) -> Dict:
        """
        Run detection on video file
        
        Args:
            video_path: Path to video file
            conf_threshold: Confidence threshold
            max_frames: Max frames to process
            on_detection: Callback for detections
            on_frame: Callback for frames
        
        Returns:
            Dict with statistics
        """
        if not self.model:
            logger.error("Model not loaded")
            return {"error": "Model not loaded"}
        
        video_path = Path(video_path)
        if not video_path.exists():
            error_msg = f"Video file not found: {video_path}"
            logger.error(error_msg)
            return {"error": error_msg}
        
        logger.info(f"Processing video file: {video_path}")
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            error_msg = f"Failed to open video: {video_path}"
            logger.error(error_msg)
            return {"error": error_msg}
        
        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(f"Video info: {width}x{height} @ {fps}fps, {total_frames} frames")
        
        frame_count = 0
        detections_total = 0
        classes_detected = set()
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # Run inference
                results = self.infer_frame(frame, conf_threshold)
                
                # Get annotated frame
                annotated_frame = results[0].plot()
                
                # Count detections
                detections = len(results[0].boxes)
                detections_total += detections
                
                # Track classes and fire callbacks
                for box in results[0].boxes:
                    cls_id = int(box.cls[0])
                    label = self.model.names[cls_id]
                    classes_detected.add(label)
                    conf_score = float(box.conf[0])
                    xyxy = box.xyxy[0].tolist()
                    
                    if on_detection:
                        on_detection({
                            "frame": frame_count,
                            "class": label,
                            "confidence": round(conf_score, 3),
                            "bbox": [round(x, 2) for x in xyxy]
                        })
                
                if on_frame:
                    on_frame(annotated_frame)
                
                if frame_count % 30 == 0:
                    logger.info(f"Processed {frame_count}/{total_frames} frames")
                
                if max_frames and frame_count >= max_frames:
                    break
        
        finally:
            cap.release()
        
        stats = {
            "status": "completed",
            "video_path": str(video_path),
            "frames_processed": frame_count,
            "total_frames": total_frames,
            "total_detections": detections_total,
            "classes_detected": list(classes_detected),
            "avg_detections_per_frame": round(detections_total / max(frame_count, 1), 2)
        }
        
        logger.info(f"Video processing completed: {stats}")
        return stats
