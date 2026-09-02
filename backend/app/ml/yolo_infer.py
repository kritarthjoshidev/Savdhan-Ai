from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)

DEFAULT_BORDER_CLASSES = ["person", "vehicle", "weapon", "backpack"]


class YOLOInference:
    """YOLO-World inference wrapper for the border-surveillance workflow."""
    
    def __init__(
        self,
        model_path: str = "yolov8s-world.pt",
        classes: List[str] | None = None,
        image_size: int = 320,
    ):
        """
        Initialize YOLO model
        
        Args:
            model_path: Path to YOLO weights (local path or 'yolov8n.pt', etc.)
        """
        try:
            resolved_path = Path(model_path)
            if not resolved_path.is_absolute() and not resolved_path.exists():
                bundled_path = Path(__file__).resolve().parents[2] / model_path
                if bundled_path.exists():
                    resolved_path = bundled_path

            self.model = YOLO(str(resolved_path))
            self.confidence_threshold = 0.35
            self.image_size = image_size
            self.classes = classes or DEFAULT_BORDER_CLASSES
            if hasattr(self.model, "set_classes"):
                self.model.set_classes(self.classes)
            logger.info("Loaded border model %s with classes: %s", resolved_path, self.classes)
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise

    def process_frame(
        self,
        frame: np.ndarray,
        conf_threshold: float = 0.35
    ) -> List[Dict[str, Any]]:
        """
        Run inference on a single frame
        
        Args:
            frame: Input frame (numpy array, BGR)
            conf_threshold: Confidence threshold for detections
            
        Returns:
            List of detections with bbox, confidence, class
        """
        try:
            results = self.model(
                frame,
                conf=conf_threshold,
                imgsz=self.image_size,
                verbose=False,
            )
            detections = []
            
            for r in results:
                for box in r.boxes:
                    conf = float(box.conf[0])
                    if conf >= conf_threshold:
                        # Get bounding box in [x, y, w, h] format
                        x, y, w, h = box.xywh[0].tolist()
                        cls = int(box.cls[0])
                        cls_name = r.names[cls]
                        
                        detection = {
                            "bbox": [x, y, w, h],
                            "confidence": conf,
                            "class": cls,
                            "class_name": cls_name
                        }
                        detections.append(detection)
            
            return detections
        except Exception as e:
            logger.error(f"Error in YOLO inference: {e}")
            return []

    @staticmethod
    def enhance_low_light(frame: np.ndarray) -> np.ndarray:
        """Apply CLAHE to the luminance channel without distorting colour."""
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        lightness, a_channel, b_channel = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(lightness)
        return cv2.cvtColor(
            cv2.merge((enhanced, a_channel, b_channel)), cv2.COLOR_LAB2BGR
        )

    def crop_detection(
        self,
        frame: np.ndarray,
        bbox: List[float]
    ) -> np.ndarray:
        """
        Crop frame using bounding box
        
        Args:
            frame: Input frame
            bbox: [x_center, y_center, width, height]
            
        Returns:
            Cropped frame
        """
        x_center, y_center, width, height = bbox
        x1 = int(x_center - width / 2)
        y1 = int(y_center - height / 2)
        x2 = int(x_center + width / 2)
        y2 = int(y_center + height / 2)
        
        # Ensure coordinates are within bounds
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(frame.shape[1], x2)
        y2 = min(frame.shape[0], y2)
        
        return frame[y1:y2, x1:x2]
