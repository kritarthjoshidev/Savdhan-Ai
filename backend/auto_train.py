#!/usr/bin/env python
"""
1-Click Automated YOLO Training Pipeline
- Frame extraction from video
- Auto-labeling using YOLO-World (zero-shot detection)
- YOLOv8n fine-tuning
- Inference on original video with annotations
"""

import os
import cv2
import json
import shutil
import yaml
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import logging

from ultralytics import YOLO
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_device():
    """Detect and return appropriate device (GPU or CPU)"""
    try:
        import torch
        if torch.cuda.is_available():
            device = 0  # Use first GPU
            logger.info(f"✓ GPU detected: {torch.cuda.get_device_name(0)}")
            return device
        else:
            logger.info("⚠ GPU not available, using CPU")
            return "cpu"
    except:
        logger.info("⚠ Could not detect GPU, using CPU")
        return "cpu"


class AutoTrainPipeline:
    """Complete automated training pipeline for video-based YOLO model"""
    
    def __init__(self, output_dir: str = "auto_train_output"):
        self.output_dir = Path(output_dir)
        self.dataset_dir = self.output_dir / "dataset"
        self.images_dir = self.dataset_dir / "images" / "train"
        self.labels_dir = self.dataset_dir / "labels" / "train"
        self.models_dir = self.output_dir / "models"
        self.inference_dir = self.output_dir / "inference"
        
        # Create directories
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.labels_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.inference_dir.mkdir(parents=True, exist_ok=True)
        
        self.job_info = {
            "start_time": datetime.now().isoformat(),
            "status": "initialized",
            "steps": {}
        }
    
    def step(self, name: str, message: str):
        """Log step progress"""
        self.job_info["steps"][name] = {
            "timestamp": datetime.now().isoformat(),
            "message": message
        }
        logger.info(f"[{name}] {message}")
    
    def extract_and_auto_label_frames(
        self, 
        video_path: str, 
        target_classes: List[str],
        frame_interval: int = 4,
        conf_threshold: float = 0.3
    ) -> int:
        """
        Extract frames from video and auto-label using YOLO-World
        
        Args:
            video_path: Path to input video
            target_classes: List of object classes to detect
            frame_interval: Extract every n-th frame
            conf_threshold: Confidence threshold for detections
            
        Returns:
            Number of frames extracted
        """
        self.step("frame_extraction", "Starting frame extraction and auto-labeling...")
        
        # Load YOLO-World model for zero-shot detection
        logger.info("Loading YOLO-World model for auto-labeling...")
        labeler_model = YOLO("yolov8s-world.pt")
        labeler_model.set_classes(target_classes)
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        frame_idx = 0
        saved_count = 0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(f"Total frames in video: {total_frames}")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Extract every n-th frame
            if frame_idx % frame_interval == 0:
                frame_filename = f"frame_{saved_count:05d}.jpg"
                img_path = self.images_dir / frame_filename
                txt_path = self.labels_dir / f"frame_{saved_count:05d}.txt"
                
                # Save frame
                cv2.imwrite(str(img_path), frame)
                h, w, _ = frame.shape
                
                # Run auto-detection
                results = labeler_model(frame, verbose=False, conf=conf_threshold)
                
                # Generate YOLO format annotation file
                with open(str(txt_path), "w") as f:
                    for box in results[0].boxes:
                        cls_id = int(box.cls[0])
                        # Normalized xywh format (YOLO standard)
                        x_center, y_center, bw, bh = box.xywhn[0].tolist()
                        f.write(f"{cls_id} {x_center} {y_center} {bw} {bh}\n")
                
                saved_count += 1
                
                if saved_count % 10 == 0:
                    logger.info(f"Processed {saved_count} frames...")
            
            frame_idx += 1
        
        cap.release()
        
        self.step(
            "frame_extraction",
            f"Extracted {saved_count} frames and auto-labeled with {len(target_classes)} classes"
        )
        
        return saved_count
    
    def generate_data_yaml(self, target_classes: List[str]):
        """Generate data.yaml for YOLO training"""
        self.step("data_yaml_generation", "Generating data.yaml...")
        
        data_yaml_path = self.dataset_dir / "data.yaml"
        yaml_content = {
            "path": str(self.dataset_dir.absolute()),
            "train": "images/train",
            "val": "images/train",  # For testing/POC
            "nc": len(target_classes),
            "names": {i: cls for i, cls in enumerate(target_classes)}
        }
        
        with open(str(data_yaml_path), "w") as f:
            yaml.dump(yaml_content, f)
        
        logger.info(f"data.yaml created at {data_yaml_path}")
        return str(data_yaml_path)
    
    def train_model(self, data_yaml_path: str, epochs: int = 15, imgsz: int = 640):
        """Train YOLO model on extracted dataset"""
        self.step("model_training", f"Starting YOLO training for {epochs} epochs...")
        
        device = get_device()
        logger.info(f"Training device: {device}")
        
        model = YOLO("yolov8n.pt")
        
        results = model.train(
            data=data_yaml_path,
            epochs=epochs,
            imgsz=imgsz,
            batch=8,
            device=device,  # Auto-detect GPU or use CPU
            patience=5,
            project=str(self.models_dir),
            name="trained_model",
            verbose=True
        )
        
        best_weights = self.models_dir / "trained_model" / "weights" / "best.pt"
        
        self.step(
            "model_training",
            f"Training completed. Best model saved at {best_weights}"
        )
        
        return str(best_weights)
    
    def run_inference_on_video(self, model_path: str, video_path: str, conf: float = 0.4):
        """Run inference on original video and generate annotated output"""
        self.step("video_inference", "Running inference on original video...")
        
        model = YOLO(model_path)
        cap = cv2.VideoCapture(video_path)
        
        # Video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        # Output video writer
        output_video_path = self.inference_dir / "output_annotated.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_video_path), fourcc, fps, (width, height))
        
        frame_count = 0
        detections_summary = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Run inference
            results = model(frame, conf=conf, verbose=False)
            
            # Get annotated frame
            annotated_frame = results[0].plot()
            
            # Record detections
            for box in results[0].boxes:
                cls_id = int(box.cls[0])
                label = model.names[cls_id]
                conf_score = float(box.conf[0])
                xyxy = box.xyxy[0].tolist()
                
                detections_summary.append({
                    "frame": frame_count,
                    "class": label,
                    "confidence": round(conf_score, 3),
                    "bbox": [round(x, 2) for x in xyxy]
                })
            
            # Write frame
            out.write(annotated_frame)
            frame_count += 1
            
            if frame_count % 30 == 0:
                logger.info(f"Processed {frame_count} frames for inference...")
        
        cap.release()
        out.release()
        
        self.step(
            "video_inference",
            f"Inference completed. Output video: {output_video_path}"
        )
        
        # Save detections summary
        detections_file = self.inference_dir / "detections.json"
        with open(str(detections_file), "w") as f:
            json.dump(detections_summary, f, indent=2)
        
        return str(output_video_path), detections_summary
    
    def save_job_info(self):
        """Save job information to JSON"""
        self.job_info["end_time"] = datetime.now().isoformat()
        
        job_info_path = self.output_dir / "job_info.json"
        with open(str(job_info_path), "w") as f:
            json.dump(self.job_info, f, indent=2)
        
        return str(job_info_path)
    
    def run_full_pipeline(
        self,
        video_path: str,
        target_classes: List[str],
        epochs: int = 15,
        frame_interval: int = 4
    ) -> Dict:
        """Execute complete pipeline"""
        try:
            self.job_info["status"] = "running"
            
            # Step 1: Extract and label frames
            frame_count = self.extract_and_auto_label_frames(
                video_path,
                target_classes,
                frame_interval=frame_interval
            )
            
            if frame_count == 0:
                raise ValueError("No frames extracted from video")
            
            # Step 2: Generate data.yaml
            data_yaml_path = self.generate_data_yaml(target_classes)
            
            # Step 3: Train model
            best_model_path = self.train_model(data_yaml_path, epochs=epochs)
            
            # Step 4: Run inference on video
            output_video, detections = self.run_inference_on_video(
                best_model_path,
                video_path
            )
            
            self.job_info["status"] = "completed"
            self.job_info["results"] = {
                "frames_extracted": frame_count,
                "classes": target_classes,
                "model_path": best_model_path,
                "output_video": output_video,
                "detections_count": len(detections),
                "dataset_path": str(self.dataset_dir)
            }
            
            # Save job info
            job_info_path = self.save_job_info()
            
            return self.job_info["results"]
            
        except Exception as e:
            self.job_info["status"] = "failed"
            self.job_info["error"] = str(e)
            self.save_job_info()
            logger.error(f"Pipeline failed: {e}")
            raise


def main():
    parser = argparse.ArgumentParser(description="1-Click Automated YOLO Training Pipeline")
    parser.add_argument("--video", type=str, required=True, help="Path to input video file")
    parser.add_argument("--classes", type=str, default="person,motorcycle,weapon,helmet",
                       help="Comma-separated list of classes to detect")
    parser.add_argument("--epochs", type=int, default=15, help="Number of training epochs")
    parser.add_argument("--frame-interval", type=int, default=4, help="Extract every n-th frame")
    parser.add_argument("--output-dir", type=str, default="auto_train_output", help="Output directory")
    
    args = parser.parse_args()
    
    # Parse classes
    target_classes = [cls.strip() for cls in args.classes.split(",")]
    
    logger.info(f"Starting automated training pipeline...")
    logger.info(f"Video: {args.video}")
    logger.info(f"Classes: {target_classes}")
    logger.info(f"Epochs: {args.epochs}")
    
    # Run pipeline
    pipeline = AutoTrainPipeline(output_dir=args.output_dir)
    results = pipeline.run_full_pipeline(
        video_path=args.video,
        target_classes=target_classes,
        epochs=args.epochs,
        frame_interval=args.frame_interval
    )
    
    logger.info("\n" + "="*60)
    logger.info("PIPELINE COMPLETED SUCCESSFULLY!")
    logger.info("="*60)
    logger.info(f"Frames extracted: {results['frames_extracted']}")
    logger.info(f"Model saved: {results['model_path']}")
    logger.info(f"Output video: {results['output_video']}")
    logger.info(f"Total detections: {results['detections_count']}")
    logger.info("="*60)


if __name__ == "__main__":
    main()
