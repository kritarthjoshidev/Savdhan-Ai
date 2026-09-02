#!/usr/bin/env python
"""
Integration Test Suite for Auto-Train Pipeline API Endpoints
Tests the complete workflow end-to-end
"""

import requests
import json
import time
import sys
from pathlib import Path


class APITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_health(self):
        """Test health endpoint"""
        print("\n[1/5] Testing Health Endpoint...")
        try:
            r = self.session.get(f"{self.base_url}/health")
            assert r.status_code == 200
            assert r.json()["status"] == "ok"
            print("✓ Health check passed")
            return True
        except Exception as e:
            print(f"✗ Health check failed: {e}")
            return False
    
    def test_incident_management(self):
        """Test incident CRUD operations"""
        print("\n[2/5] Testing Incident Management...")
        try:
            # Create incident
            incident_data = {
                "source_cam": "camera_01",
                "bbox": {"x_min": 0, "y_min": 0, "x_max": 100, "y_max": 100},
                "snapshot_path": "/snapshots/test.jpg",
                "confidence": 0.95,
                "track_id": 1,
                "meta": {"class": "person", "alert_type": "test"}
            }
            
            r = self.session.post(
                f"{self.base_url}/api/v1/incidents",
                json=incident_data
            )
            assert r.status_code == 200 or r.status_code == 201
            incident = r.json()
            incident_id = incident["id"]
            print(f"✓ Created incident (ID={incident_id})")
            
            # List incidents
            r = self.session.get(f"{self.base_url}/api/v1/incidents?limit=10")
            assert r.status_code == 200
            print(f"✓ Listed incidents ({len(r.json().get('incidents', []))} found)")
            
            # Get specific incident
            r = self.session.get(f"{self.base_url}/api/v1/incidents/{incident_id}")
            assert r.status_code == 200
            print(f"✓ Retrieved incident details")
            
            # Update incident
            r = self.session.patch(
                f"{self.base_url}/api/v1/incidents/{incident_id}",
                json={"status": "reviewed"}
            )
            assert r.status_code == 200
            print(f"✓ Updated incident status")
            
            return True
        except Exception as e:
            print(f"✗ Incident management failed: {e}")
            return False
    
    def test_models_list(self):
        """Test model listing"""
        print("\n[3/5] Testing Model Management...")
        try:
            r = self.session.get(f"{self.base_url}/api/v1/models")
            assert r.status_code == 200
            models = r.json()
            print(f"✓ Listed models ({len(models)} found)")
            return True
        except Exception as e:
            print(f"✗ Model listing failed: {e}")
            return False
    
    def test_auto_train_endpoints(self):
        """Test auto-train endpoints"""
        print("\n[4/5] Testing Auto-Train Endpoints...")
        
        # Check if endpoints are registered
        try:
            # Get API docs to verify endpoints exist
            r = self.session.get(f"{self.base_url}/openapi.json")
            assert r.status_code == 200
            openapi = r.json()
            
            paths = openapi.get("paths", {})
            
            # Check for auto-train endpoints
            has_post_train = "/api/v1/models/auto-train" in paths
            has_get_status = "/api/v1/models/auto-train/status/{job_id}" in paths
            has_download = "/api/v1/models/auto-train/download/{job_id}" in paths
            
            if has_post_train and has_get_status and has_download:
                print("✓ Auto-train endpoints registered")
                print("  - POST /api/v1/models/auto-train")
                print("  - GET /api/v1/models/auto-train/status/{job_id}")
                print("  - GET /api/v1/models/auto-train/download/{job_id}")
                return True
            else:
                print(f"✗ Missing endpoints:")
                print(f"  - POST endpoint: {has_post_train}")
                print(f"  - GET status endpoint: {has_get_status}")
                print(f"  - GET download endpoint: {has_download}")
                return False
        except Exception as e:
            print(f"✗ Auto-train verification failed: {e}")
            return False
    
    def test_api_docs(self):
        """Test API documentation availability"""
        print("\n[5/5] Testing API Documentation...")
        try:
            # Swagger UI
            r = self.session.get(f"{self.base_url}/docs")
            assert r.status_code == 200
            print("✓ Swagger UI available at /docs")
            
            # OpenAPI schema
            r = self.session.get(f"{self.base_url}/openapi.json")
            assert r.status_code == 200
            schema = r.json()
            print(f"✓ OpenAPI schema available ({len(schema.get('paths', {}))} paths)")
            
            # ReDoc
            r = self.session.get(f"{self.base_url}/redoc")
            assert r.status_code == 200
            print("✓ ReDoc available at /redoc")
            
            return True
        except Exception as e:
            print(f"✗ API documentation check failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("="*70)
        print("🧪 AUTO-TRAIN PIPELINE - INTEGRATION TEST SUITE")
        print("="*70)
        
        print(f"\nBackend URL: {self.base_url}")
        
        # Run tests
        results = {
            "health": self.test_health(),
            "incidents": self.test_incident_management(),
            "models": self.test_models_list(),
            "auto_train": self.test_auto_train_endpoints(),
            "docs": self.test_api_docs(),
        }
        
        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"  {status:10} - {test_name.replace('_', ' ').title()}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All tests passed! Backend is ready.")
            return True
        else:
            print(f"\n⚠ {total - passed} test(s) failed.")
            return False


def create_sample_video():
    """Create a sample video for testing (if not exists)"""
    import cv2
    import numpy as np
    
    video_path = Path("sample_video.mp4")
    
    if video_path.exists():
        print(f"✓ Sample video already exists: {video_path}")
        return str(video_path)
    
    print("Creating sample video for testing...")
    
    # Video parameters
    fps = 30
    duration = 5  # seconds
    width, height = 640, 480
    frame_count = fps * duration
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))
    
    # Generate frames
    for i in range(frame_count):
        # Create frame with some content
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add gradient
        for y in range(height):
            frame[y, :] = [int(255 * i / frame_count), 100, 150]
        
        # Add moving circle
        cx = int(width * (0.3 + 0.4 * i / frame_count))
        cy = int(height * 0.5)
        cv2.circle(frame, (cx, cy), 30, (0, 255, 255), -1)
        
        # Add text
        cv2.putText(
            frame,
            f"Sample Video - Frame {i+1}/{frame_count}",
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )
        
        out.write(frame)
    
    out.release()
    print(f"✓ Sample video created: {video_path}")
    
    return str(video_path)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Auto-Train Pipeline Integration Tests"
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:8000",
        help="Backend API URL"
    )
    parser.add_argument(
        "--create-sample",
        action="store_true",
        help="Create sample video for testing"
    )
    
    args = parser.parse_args()
    
    # Create sample video if requested
    if args.create_sample:
        try:
            create_sample_video()
        except Exception as e:
            print(f"⚠ Could not create sample video: {e}")
            print("  (OpenCV may need to be installed: pip install opencv-python)")
    
    # Run tests
    tester = APITester(base_url=args.url)
    success = tester.run_all_tests()
    
    print("\n" + "="*70)
    print("NEXT STEPS:")
    print("="*70)
    print("\n1. Train a model (1-click):")
    print("   python auto_train.py --video sample_video.mp4 --classes person --epochs 5")
    print("\n2. Or use the API:")
    print("   curl -X POST http://localhost:8000/api/v1/models/auto-train \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"video_path\":\"sample_video.mp4\",\"classes\":[\"person\"],\"epochs\":5}'")
    print("\n3. Check progress:")
    print("   curl http://localhost:8000/api/v1/models/auto-train/status/{job_id}")
    print("\n" + "="*70 + "\n")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
