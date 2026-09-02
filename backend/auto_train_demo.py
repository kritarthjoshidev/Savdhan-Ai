#!/usr/bin/env python
"""
Demo/Test script for 1-Click Auto-Train Pipeline
Shows how to use the pipeline both locally and via API
"""

import requests
import json
import time
import argparse
from pathlib import Path


def demo_local_pipeline(video_path: str, classes: list, epochs: int):
    """Demo: Run pipeline locally without API"""
    print("\n" + "="*70)
    print("DEMO 1: LOCAL AUTO-TRAIN PIPELINE (Direct Script)")
    print("="*70 + "\n")
    
    print(f"Video: {video_path}")
    print(f"Classes: {classes}")
    print(f"Epochs: {epochs}\n")
    
    print("Command to run:")
    print(f"  python auto_train.py \\")
    print(f"    --video {video_path} \\")
    print(f"    --classes {','.join(classes)} \\")
    print(f"    --epochs {epochs}")
    
    print("\nThis will:")
    print("  1. Extract frames from video")
    print("  2. Auto-label using YOLO-World")
    print("  3. Train YOLOv8n model")
    print("  4. Run inference on original video")
    print("  5. Save annotated output video\n")


def demo_api_pipeline(api_url: str, video_path: str, classes: list, epochs: int):
    """Demo: Run pipeline via FastAPI endpoints"""
    print("\n" + "="*70)
    print("DEMO 2: AUTO-TRAIN VIA FASTAPI ENDPOINTS")
    print("="*70 + "\n")
    
    # Make sure backend is running
    try:
        r = requests.get(f"{api_url}/health", timeout=2)
        print(f"✓ Backend is running at {api_url}\n")
    except:
        print(f"✗ Backend not running at {api_url}")
        print(f"  Start it with: python run_backend.py\n")
        return
    
    # Step 1: Submit training job
    print("Step 1: Submitting training job...")
    payload = {
        "video_path": video_path,
        "classes": classes,
        "epochs": epochs,
        "frame_interval": 4
    }
    
    print(f"  POST {api_url}/api/v1/models/auto-train")
    print(f"  Payload: {json.dumps(payload, indent=2)}\n")
    
    r = requests.post(
        f"{api_url}/api/v1/models/auto-train",
        json=payload
    )
    
    if r.status_code != 200:
        print(f"✗ Error: {r.status_code}")
        print(f"  {r.text}\n")
        return
    
    response = r.json()
    job_id = response["job_id"]
    
    print(f"✓ Job submitted successfully!")
    print(f"  Job ID: {job_id}")
    print(f"  Status: {response['status']}")
    print(f"  Message: {response['message']}\n")
    
    # Step 2: Poll job status
    print("Step 2: Monitoring training progress...\n")
    
    max_wait = 3600  # 1 hour timeout
    poll_interval = 5  # Check every 5 seconds
    elapsed = 0
    
    while elapsed < max_wait:
        r = requests.get(f"{api_url}/api/v1/models/auto-train/status/{job_id}")
        
        if r.status_code != 200:
            print(f"✗ Error checking status: {r.status_code}\n")
            break
        
        status = r.json()
        
        print(f"[{time.strftime('%H:%M:%S')}] Status: {status['status'].upper()}")
        print(f"  Progress: {status['progress']}%")
        print(f"  Message: {status['message']}")
        
        if status["status"] == "completed":
            print("\n✓ Training completed successfully!\n")
            print("Results:")
            for key, value in status["results"].items():
                print(f"  {key}: {value}")
            break
        
        elif status["status"] == "failed":
            print(f"\n✗ Training failed!")
            print(f"  Error: {status['error']}\n")
            break
        
        # Wait before next poll
        time.sleep(poll_interval)
        elapsed += poll_interval
        print()
    
    if elapsed >= max_wait:
        print(f"✗ Training timeout after {max_wait} seconds\n")


def demo_curl_commands(video_path: str, classes: list):
    """Show curl commands for API testing"""
    print("\n" + "="*70)
    print("DEMO 3: CURL COMMANDS (For Testing via Terminal)")
    print("="*70 + "\n")
    
    # Submit job
    payload = {
        "video_path": video_path,
        "classes": classes,
        "epochs": 15,
        "frame_interval": 4
    }
    
    print("1. Submit training job:")
    print(f"\ncurl -X POST http://localhost:8000/api/v1/models/auto-train \\")
    print(f"  -H 'Content-Type: application/json' \\")
    print(f"  -d '{json.dumps(payload)}'")
    print("\nReturns: { \"job_id\": \"abc12345\", ... }")
    
    print("\n" + "-"*70 + "\n")
    
    print("2. Check job status (replace abc12345 with actual job_id):")
    print(f"\ncurl http://localhost:8000/api/v1/models/auto-train/status/abc12345")
    print("\nReturns: { \"job_id\": \"abc12345\", \"status\": \"running\", ... }")
    
    print("\n" + "-"*70 + "\n")
    
    print("3. Download results (after job completes):")
    print(f"\ncurl http://localhost:8000/api/v1/models/auto-train/download/abc12345")
    print("\nReturns: { \"model_path\": \"...\", \"output_video\": \"...\", ... }")


def demo_python_client(video_path: str, classes: list):
    """Show Python code for API client"""
    print("\n" + "="*70)
    print("DEMO 4: PYTHON CLIENT CODE")
    print("="*70 + "\n")
    
    code = '''
import requests
import time

# Configuration
API_URL = "http://localhost:8000"
VIDEO_PATH = "sample.mp4"
CLASSES = ["person", "motorcycle", "weapon"]
EPOCHS = 15

# Step 1: Submit training job
print("Submitting training job...")
response = requests.post(
    f"{API_URL}/api/v1/models/auto-train",
    json={
        "video_path": VIDEO_PATH,
        "classes": CLASSES,
        "epochs": EPOCHS,
        "frame_interval": 4
    }
)
job_id = response.json()["job_id"]
print(f"Job ID: {job_id}")

# Step 2: Poll status until completion
while True:
    status_response = requests.get(
        f"{API_URL}/api/v1/models/auto-train/status/{job_id}"
    )
    status = status_response.json()
    
    print(f"Status: {status['status']} | Progress: {status['progress']}%")
    
    if status["status"] == "completed":
        print("Training completed!")
        print(f"Model: {status['results']['model_path']}")
        print(f"Output Video: {status['results']['output_video']}")
        break
    elif status["status"] == "failed":
        print(f"Training failed: {status['error']}")
        break
    
    time.sleep(5)

# Step 3: Download results
download_response = requests.get(
    f"{API_URL}/api/v1/models/auto-train/download/{job_id}"
)
results = download_response.json()
print(f"Results: {results}")
    '''
    
    print(code)


def main():
    parser = argparse.ArgumentParser(description="Auto-Train Pipeline Demo")
    parser.add_argument("--demo", choices=["local", "api", "curl", "python", "all"], 
                       default="all", help="Which demo to run")
    parser.add_argument("--video", type=str, default="sample.mp4", help="Video file path")
    parser.add_argument("--classes", type=str, default="person,motorcycle,weapon,helmet",
                       help="Comma-separated class names")
    parser.add_argument("--epochs", type=int, default=15, help="Training epochs")
    parser.add_argument("--api-url", type=str, default="http://localhost:8000",
                       help="Backend API URL")
    
    args = parser.parse_args()
    
    classes = [c.strip() for c in args.classes.split(",")]
    
    print("\n" + "="*70)
    print("🎯 SAWDHAN AI - AUTO-TRAIN PIPELINE DEMO")
    print("="*70)
    
    if args.demo in ["local", "all"]:
        demo_local_pipeline(args.video, classes, args.epochs)
    
    if args.demo in ["api", "all"]:
        demo_api_pipeline(args.api_url, args.video, classes, args.epochs)
    
    if args.demo in ["curl", "all"]:
        demo_curl_commands(args.video, classes)
    
    if args.demo in ["python", "all"]:
        demo_python_client(args.video, classes)
    
    print("\n" + "="*70)
    print("QUICK START CHECKLIST:")
    print("="*70)
    print("\n1. Make sure backend is running:")
    print("   python run_backend.py")
    print("\n2. Install YOLO-World model (one-time):")
    print("   python -c \"from ultralytics import YOLO; YOLO('yolov8s-world.pt')\"")
    print("\n3. Run auto-train pipeline:")
    print("   python auto_train.py --video your_video.mp4 --classes person,motorcycle --epochs 15")
    print("\n4. Or use API:")
    print("   curl -X POST http://localhost:8000/api/v1/models/auto-train \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"video_path\":\"your_video.mp4\",\"classes\":[\"person\"],\"epochs\":15}'")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
