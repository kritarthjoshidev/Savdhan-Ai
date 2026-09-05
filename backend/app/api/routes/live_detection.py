"""
Live detection API routes (webcam, RTSP, video file)
"""

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import logging
import cv2
import base64
from typing import Optional, Dict
from pathlib import Path
import json
import asyncio

from app.services.live_detector import LiveDetector
from app.services.camera_manager import CameraManager, get_camera_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/live", tags=["live_detection"])

# Global detector instance
live_detector = None


def get_live_detector():
    """Get or create live detector instance"""
    global live_detector
    if live_detector is None:
        try:
            live_detector = LiveDetector("yolov8s-world.pt")
        except Exception as e:
            logger.error(f"Failed to initialize live detector: {e}")
    return live_detector


# ============= Pydantic Models =============

class WebcamDetectionRequest(BaseModel):
    """Webcam detection request"""
    device_id: int = 0
    conf_threshold: float = 0.5
    max_frames: Optional[int] = None
    stream_fps: int = 30  # FPS to send via WebSocket


class RTSPDetectionRequest(BaseModel):
    """RTSP stream detection request"""
    rtsp_url: str  # e.g., rtsp://username:password@192.168.1.100:554/stream
    conf_threshold: float = 0.5
    max_frames: Optional[int] = None
    stream_fps: int = 30


class VideoDetectionRequest(BaseModel):
    """Video file detection request"""
    video_path: str
    conf_threshold: float = 0.5
    max_frames: Optional[int] = None


class DetectionResponse(BaseModel):
    """Detection response"""
    status: str
    message: str
    stats: Optional[Dict] = None


# ============= Webcam Endpoints =============

@router.post("/webcam/detect", response_model=DetectionResponse)
async def detect_from_webcam(request: WebcamDetectionRequest):
    """
    Run real-time detection on webcam
    
    Example:
        POST /api/v1/live/webcam/detect
        {
            "device_id": 0,
            "conf_threshold": 0.5,
            "max_frames": 100,
            "stream_fps": 30
        }
    """
    detector = get_live_detector()
    if not detector or not detector.model:
        raise HTTPException(status_code=500, detail="Model not initialized")
    
    try:
        stats = detector.detect_from_webcam(
            conf_threshold=request.conf_threshold,
            device_id=request.device_id,
            max_frames=request.max_frames
        )
        
        if "error" in stats:
            raise HTTPException(status_code=400, detail=stats["error"])
        
        return DetectionResponse(
            status="success",
            message="Webcam detection completed",
            stats=stats
        )
    
    except Exception as e:
        logger.error(f"Webcam detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/webcam/available")
async def check_webcam_available(device_id: int = Query(0, description="Webcam device ID")):
    """
    Check if webcam is available
    
    Example:
        GET /api/v1/live/webcam/available?device_id=0
    """
    try:
        cap = cv2.VideoCapture(device_id)
        available = cap.isOpened()
        
        if available:
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            cap.release()
            
            return {
                "status": "available",
                "device_id": device_id,
                "resolution": f"{width}x{height}",
                "fps": fps
            }
        else:
            cap.release()
            return {
                "status": "unavailable",
                "device_id": device_id,
                "message": "Webcam not found or not accessible"
            }
    
    except Exception as e:
        logger.error(f"Webcam check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= RTSP Endpoints =============

@router.post("/rtsp/detect", response_model=DetectionResponse)
async def detect_from_rtsp(request: RTSPDetectionRequest):
    """
    Run real-time detection on RTSP stream (CCTV)
    
    Example:
        POST /api/v1/live/rtsp/detect
        {
            "rtsp_url": "rtsp://admin:password@192.168.1.100:554/stream",
            "conf_threshold": 0.5,
            "max_frames": null,
            "stream_fps": 30
        }
    """
    detector = get_live_detector()
    try:
        CameraManager.validate_url(request.rtsp_url)
        if not request.rtsp_url.strip().lower().startswith("rtsp://"):
            raise ValueError("This endpoint requires an rtsp:// URL")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not detector or not detector.model:
        raise HTTPException(status_code=500, detail="Model not initialized")
    
    try:
        stats = detector.detect_from_rtsp(
            rtsp_url=request.rtsp_url,
            conf_threshold=request.conf_threshold,
            max_frames=request.max_frames
        )
        
        if "error" in stats:
            raise HTTPException(status_code=400, detail=stats["error"])
        
        return DetectionResponse(
            status="success",
            message="RTSP detection completed",
            stats=stats
        )
    
    except Exception as e:
        logger.error(f"RTSP detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rtsp/test", response_model=Dict)
async def test_rtsp_connection(rtsp_url: str = Query(..., description="RTSP URL to test")):
    """
    Test RTSP connection without running full detection
    
    Example:
        POST /api/v1/live/rtsp/test?rtsp_url=rtsp://admin:password@192.168.1.100:554/stream
    """
    try:
        CameraManager.validate_url(rtsp_url)
        if not rtsp_url.strip().lower().startswith("rtsp://"):
            raise ValueError("This endpoint requires an rtsp:// URL")
        CameraManager.check_rtsp_endpoint(rtsp_url)
        cap = cv2.VideoCapture(rtsp_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
        
        # Try to read first frame
        connected = False
        for _ in range(10):
            ret, frame = cap.read()
            if ret:
                connected = True
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                cap.release()
                
                return {
                    "status": "connected",
                    "rtsp_url": rtsp_url[:30] + "...",
                    "resolution": f"{width}x{height}",
                    "fps": fps,
                    "message": "RTSP stream is accessible"
                }
            cv2.waitKey(100)
        
        cap.release()
        return {
            "status": "failed",
            "rtsp_url": rtsp_url[:30] + "...",
            "message": "Could not connect to RTSP stream"
        }
    
    except (ValueError, ConnectionError) as e:
        return {"status": "invalid", "message": str(e)}
    except Exception as e:
        logger.error(f"RTSP test error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


# ============= Video File Endpoints =============

@router.post("/video/detect", response_model=DetectionResponse)
async def detect_from_video_file(request: VideoDetectionRequest):
    """
    Run detection on video file
    
    Example:
        POST /api/v1/live/video/detect
        {
            "video_path": "./test_video.mp4",
            "conf_threshold": 0.5,
            "max_frames": null
        }
    """
    detector = get_live_detector()
    if not detector or not detector.model:
        raise HTTPException(status_code=500, detail="Model not initialized")
    
    # Verify file exists
    video_path = Path(request.video_path)
    if not video_path.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Video file not found: {request.video_path}"
        )
    
    try:
        stats = detector.detect_from_file(
            video_path=str(video_path),
            conf_threshold=request.conf_threshold,
            max_frames=request.max_frames
        )
        
        if "error" in stats:
            raise HTTPException(status_code=400, detail=stats["error"])
        
        return DetectionResponse(
            status="success",
            message="Video detection completed",
            stats=stats
        )
    
    except Exception as e:
        logger.error(f"Video detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= WebSocket Live Streaming =============

class ConnectionManager:
    """Manage WebSocket connections for live streaming"""
    def __init__(self):
        self.active_connections: list = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


live_stream_manager = ConnectionManager()


def _frame_payload(detector, frame, frame_count: int) -> dict:
    """Run inference and make one compact JPEG payload for browser live view."""
    results = detector.infer_frame(frame, conf_threshold=0.35)
    detections = []
    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        detections.append({
            "class": detector.model.names[cls_id],
            "confidence": round(float(box.conf[0]), 3),
            "bbox": [round(value, 1) for value in box.xyxy[0].tolist()],
        })
    annotated = results[0].plot()
    height, width = annotated.shape[:2]
    if width > 960:
        scale = 960 / width
        annotated = cv2.resize(annotated, (960, max(2, int(height * scale))))
    encoded, jpeg = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 78])
    if not encoded:
        raise RuntimeError("Could not encode live camera frame")
    return {
        "type": "frame",
        "frame": frame_count,
        "detections": detections,
        "frame_jpeg": base64.b64encode(jpeg.tobytes()).decode("ascii"),
    }


async def _stream_capture(websocket: WebSocket, cap, detector, source_label: str) -> None:
    """Send annotated preview frames and detection metadata on one websocket."""
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
    await websocket.send_json({
        "type": "stream_info",
        "resolution": f"{width}x{height}",
        "fps": round(fps, 1),
        "status": "streaming",
        "source": source_label,
    })
    frame_count = 0
    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            await websocket.send_json({"type": "stream_end", "reason": "camera_disconnected"})
            return
        frame_count += 1
        await websocket.send_json(_frame_payload(detector, frame, frame_count))
        # Yield to disconnect / ping handling between CPU-heavy inferences.
        await asyncio.sleep(0)


@router.websocket("/webcam/stream")
async def websocket_webcam_stream(websocket: WebSocket, device_id: int = 0):
    """
    WebSocket endpoint for live webcam streaming with real-time detection
    
    Usage:
        ws://localhost:8000/api/v1/live/webcam/stream?device_id=0
    
    Receives JSON messages with detections in real-time
    """
    await live_stream_manager.connect(websocket)
    
    detector = get_live_detector()
    if not detector or not detector.model:
        await websocket.send_json({"error": "Model not initialized"})
        await live_stream_manager.disconnect(websocket)
        return
    
    try:
        # Open webcam
        cap = cv2.VideoCapture(device_id)
        if not cap.isOpened():
            await websocket.send_json({"error": f"Failed to open webcam {device_id}"})
            await live_stream_manager.disconnect(websocket)
            return
        
        # Get camera properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        await websocket.send_json({
            "type": "stream_info",
            "resolution": f"{width}x{height}",
            "fps": fps,
            "status": "streaming"
        })
        
        frame_count = 0
        detection_count = 0
        
        while True:
            # Check for incoming messages (e.g., stop command)
            try:
                await websocket.receive_json()  # Non-blocking check
            except:
                pass
            
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Run inference
            results = detector.infer_frame(frame, conf_threshold=0.5)
            
            # Prepare detection data
            detections = []
            for box in results[0].boxes:
                cls_id = int(box.cls[0])
                label = detector.model.names[cls_id]
                conf_score = float(box.conf[0])
                xyxy = box.xyxy[0].tolist()
                
                detections.append({
                    "class": label,
                    "confidence": round(conf_score, 3),
                    "bbox": [round(x, 2) for x in xyxy]
                })
                detection_count += 1
            
            # Send detection data
            await websocket.send_json({
                "type": "detection",
                "frame": frame_count,
                "detections": detections,
                "detection_count": len(detections)
            })
        
        cap.release()
        
        await websocket.send_json({
            "type": "stream_end",
            "frames_processed": frame_count,
            "total_detections": detection_count
        })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected - webcam {device_id}")
        await live_stream_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
        await live_stream_manager.disconnect(websocket)


@router.websocket("/rtsp/stream")
async def websocket_rtsp_stream(websocket: WebSocket, rtsp_url: str = Query(...)):
    """
    WebSocket endpoint for live RTSP streaming with real-time detection
    
    Usage:
        ws://localhost:8000/api/v1/live/rtsp/stream?rtsp_url=rtsp://admin:password@ip:port/stream
    
    Receives JSON messages with detections in real-time
    """
    await live_stream_manager.connect(websocket)

    try:
        CameraManager.validate_url(rtsp_url)
        if not rtsp_url.strip().lower().startswith("rtsp://"):
            raise ValueError("This endpoint requires an rtsp:// URL")
        CameraManager.check_rtsp_endpoint(rtsp_url)
    except (ValueError, ConnectionError) as exc:
        await websocket.send_json({"type": "error", "error": str(exc)})
        await live_stream_manager.disconnect(websocket)
        return
    
    detector = get_live_detector()
    if not detector or not detector.model:
        await websocket.send_json({"error": "Model not initialized"})
        await live_stream_manager.disconnect(websocket)
        return
    
    try:
        # Connect to RTSP stream
        cap = cv2.VideoCapture(rtsp_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Wait for connection
        connected = False
        for _ in range(30):
            ret, frame = cap.read()
            if ret:
                connected = True
                break
            cv2.waitKey(100)
        
        if not connected:
            await websocket.send_json({
                "error": f"Failed to connect to RTSP stream: {rtsp_url[:30]}"
            })
            cap.release()
            await live_stream_manager.disconnect(websocket)
            return
        
        # Get stream properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        await websocket.send_json({
            "type": "stream_info",
            "resolution": f"{width}x{height}",
            "fps": fps,
            "status": "streaming",
            "rtsp_url": rtsp_url[:30] + "..."
        })
        
        frame_count = 0
        detection_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Run inference
            results = detector.infer_frame(frame, conf_threshold=0.5)
            
            # Prepare detection data
            detections = []
            for box in results[0].boxes:
                cls_id = int(box.cls[0])
                label = detector.model.names[cls_id]
                conf_score = float(box.conf[0])
                xyxy = box.xyxy[0].tolist()
                
                detections.append({
                    "class": label,
                    "confidence": round(conf_score, 3),
                    "bbox": [round(x, 2) for x in xyxy]
                })
                detection_count += 1
            
            # Send an annotated browser-preview frame plus detection data.
            annotated = results[0].plot()
            encoded, jpeg = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 78])
            if not encoded:
                continue
            await websocket.send_json({
                "type": "frame",
                "frame": frame_count,
                "detections": detections,
                "detection_count": len(detections),
                "frame_jpeg": base64.b64encode(jpeg.tobytes()).decode("ascii"),
            })
        
        cap.release()
        
        await websocket.send_json({
            "type": "stream_end",
            "frames_processed": frame_count,
            "total_detections": detection_count
        })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected - RTSP")
        await live_stream_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
        await live_stream_manager.disconnect(websocket)


@router.websocket("/camera/stream")
async def websocket_registered_camera_stream(websocket: WebSocket, camera_id: str = Query(...)):
    """Preview a registered phone/CCTV camera without exposing its URL to React."""
    await websocket.accept()
    cap = None
    try:
        camera = get_camera_manager().get(camera_id)
        if not camera:
            await websocket.send_json({"type": "error", "error": "Camera not found"})
            return
        detector = get_live_detector()
        if not detector or not detector.model:
            await websocket.send_json({"type": "error", "error": "Model not initialized"})
            return
        cap = cv2.VideoCapture(camera["stream_url"])
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not cap.isOpened():
            await websocket.send_json({"type": "error", "error": "Could not open this camera stream"})
            return
        await _stream_capture(websocket, cap, detector, camera["name"])
    except WebSocketDisconnect:
        logger.info("Camera-preview client disconnected: %s", camera_id)
    except Exception as exc:
        logger.exception("Camera-preview error for %s", camera_id)
        try:
            await websocket.send_json({"type": "error", "error": str(exc)})
        except Exception:
            pass
    finally:
        if cap is not None:
            cap.release()
