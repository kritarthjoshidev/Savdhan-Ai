"""
Test client for live detection APIs
Usage: python test_live_detection.py
"""

import requests
import json
import asyncio
import websockets
import cv2
from typing import Optional

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1/live"


class LiveDetectionTester:
    """Test live detection endpoints"""
    
    def __init__(self, base_url: str = API_URL):
        self.base_url = base_url
    
    # ============= Webcam Tests =============
    
    def test_webcam_available(self, device_id: int = 0):
        """Test if webcam is available"""
        print(f"\n📷 Testing Webcam Availability (device {device_id})...")
        try:
            response = requests.get(
                f"{self.base_url}/webcam/available",
                params={"device_id": device_id}
            )
            result = response.json()
            print(f"✓ Result: {json.dumps(result, indent=2)}")
            return result
        except Exception as e:
            print(f"✗ Error: {e}")
            return None
    
    def test_webcam_detect(self, device_id: int = 0, max_frames: Optional[int] = 50):
        """Test real-time webcam detection"""
        print(f"\n📷 Testing Webcam Detection (device {device_id}, max {max_frames} frames)...")
        try:
            payload = {
                "device_id": device_id,
                "conf_threshold": 0.5,
                "max_frames": max_frames,
                "stream_fps": 30
            }
            
            print(f"Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                f"{self.base_url}/webcam/detect",
                json=payload
            )
            result = response.json()
            print(f"✓ Result: {json.dumps(result, indent=2)}")
            return result
        except Exception as e:
            print(f"✗ Error: {e}")
            return None
    
    # ============= RTSP Tests =============
    
    def test_rtsp_connection(self, rtsp_url: str):
        """Test RTSP stream connection"""
        print(f"\n📹 Testing RTSP Connection...")
        print(f"URL: {rtsp_url[:40]}...")
        
        try:
            response = requests.post(
                f"{self.base_url}/rtsp/test",
                params={"rtsp_url": rtsp_url}
            )
            result = response.json()
            print(f"✓ Result: {json.dumps(result, indent=2)}")
            return result
        except Exception as e:
            print(f"✗ Error: {e}")
            return None
    
    def test_rtsp_detect(self, rtsp_url: str, max_frames: Optional[int] = 50):
        """Test RTSP detection"""
        print(f"\n📹 Testing RTSP Detection (max {max_frames} frames)...")
        try:
            payload = {
                "rtsp_url": rtsp_url,
                "conf_threshold": 0.5,
                "max_frames": max_frames,
                "stream_fps": 30
            }
            
            print(f"URL: {rtsp_url[:40]}...")
            
            response = requests.post(
                f"{self.base_url}/rtsp/detect",
                json=payload,
                timeout=300
            )
            result = response.json()
            print(f"✓ Result: {json.dumps(result, indent=2)}")
            return result
        except Exception as e:
            print(f"✗ Error: {e}")
            return None
    
    # ============= Video File Tests =============
    
    def test_video_detect(self, video_path: str, max_frames: Optional[int] = None):
        """Test video file detection"""
        print(f"\n🎬 Testing Video Detection: {video_path}")
        try:
            payload = {
                "video_path": video_path,
                "conf_threshold": 0.5,
                "max_frames": max_frames
            }
            
            response = requests.post(
                f"{self.base_url}/video/detect",
                json=payload,
                timeout=300
            )
            result = response.json()
            print(f"✓ Result: {json.dumps(result, indent=2)}")
            return result
        except Exception as e:
            print(f"✗ Error: {e}")
            return None
    
    # ============= WebSocket Tests =============
    
    async def test_webcam_websocket(self, device_id: int = 0, frames: int = 30):
        """Test WebSocket webcam streaming"""
        print(f"\n🔗 Testing Webcam WebSocket (device {device_id}, {frames} frames)...")
        
        ws_url = f"ws://localhost:8000/api/v1/live/webcam/stream?device_id={device_id}"
        
        try:
            async with websockets.connect(ws_url) as websocket:
                frame_count = 0
                total_detections = 0
                
                while True:
                    try:
                        message = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=5
                        )
                        data = json.loads(message)
                        
                        if data.get("type") == "stream_info":
                            print(f"✓ Stream connected: {data.get('resolution')} @ {data.get('fps')}fps")
                        
                        elif data.get("type") == "detection":
                            frame_count = data.get("frame", 0)
                            det_count = data.get("detection_count", 0)
                            total_detections += det_count
                            
                            if det_count > 0:
                                print(f"  Frame {frame_count}: {det_count} detections")
                                for det in data.get("detections", []):
                                    print(f"    - {det['class']} ({det['confidence']})")
                            
                            if frame_count >= frames:
                                break
                        
                        elif data.get("type") == "stream_end":
                            print(f"✓ Stream ended: {data}")
                            break
                        
                        elif "error" in data:
                            print(f"✗ Error: {data['error']}")
                            break
                    
                    except asyncio.TimeoutError:
                        print("⏱ Timeout waiting for message")
                        break
                
                print(f"✓ WebSocket test completed: {total_detections} total detections")
                return {"status": "success", "frames": frame_count, "detections": total_detections}
        
        except Exception as e:
            print(f"✗ WebSocket error: {e}")
            return None
    
    async def test_rtsp_websocket(self, rtsp_url: str, frames: int = 30):
        """Test WebSocket RTSP streaming"""
        print(f"\n🔗 Testing RTSP WebSocket ({frames} frames)...")
        print(f"URL: {rtsp_url[:40]}...")
        
        ws_url = f"ws://localhost:8000/api/v1/live/rtsp/stream?rtsp_url={rtsp_url}"
        
        try:
            async with websockets.connect(ws_url) as websocket:
                frame_count = 0
                total_detections = 0
                
                while True:
                    try:
                        message = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=10
                        )
                        data = json.loads(message)
                        
                        if data.get("type") == "stream_info":
                            print(f"✓ Stream connected: {data.get('resolution')} @ {data.get('fps')}fps")
                        
                        elif data.get("type") == "detection":
                            frame_count = data.get("frame", 0)
                            det_count = data.get("detection_count", 0)
                            total_detections += det_count
                            
                            if det_count > 0:
                                print(f"  Frame {frame_count}: {det_count} detections")
                            
                            if frame_count >= frames:
                                break
                        
                        elif data.get("type") == "stream_end":
                            print(f"✓ Stream ended")
                            break
                        
                        elif "error" in data:
                            print(f"✗ Error: {data['error']}")
                            break
                    
                    except asyncio.TimeoutError:
                        print("⏱ Timeout waiting for message")
                        break
                
                print(f"✓ WebSocket test completed: {total_detections} total detections")
                return {"status": "success", "frames": frame_count, "detections": total_detections}
        
        except Exception as e:
            print(f"✗ WebSocket error: {e}")
            return None


def main():
    """Run all tests"""
    print("="*60)
    print("Live Detection API Test Suite")
    print("="*60)
    
    tester = LiveDetectionTester()
    
    # Test 1: Check webcam availability
    print("\n[TEST 1] Webcam Availability")
    print("-" * 60)
    tester.test_webcam_available(device_id=0)
    
    # Test 2: Webcam detection (short)
    print("\n[TEST 2] Webcam Detection (10 frames)")
    print("-" * 60)
    tester.test_webcam_detect(device_id=0, max_frames=10)
    
    # Test 3: WebSocket webcam (if asyncio available)
    print("\n[TEST 3] Webcam WebSocket Streaming (10 frames)")
    print("-" * 60)
    try:
        asyncio.run(tester.test_webcam_websocket(device_id=0, frames=10))
    except Exception as e:
        print(f"Skipping WebSocket test: {e}")
    
    # Test 4: RTSP connection test (example URL)
    print("\n[TEST 4] RTSP Connection Test (example)")
    print("-" * 60)
    example_rtsp = "rtsp://admin:password@192.168.1.100:554/stream"
    print(f"Note: Replace with your actual RTSP URL")
    print(f"Example: {example_rtsp}")
    
    # Test 5: Video file detection (if video exists)
    print("\n[TEST 5] Video File Detection")
    print("-" * 60)
    test_video = "./test_video.mp4"
    print(f"Looking for: {test_video}")
    tester.test_video_detect(video_path=test_video, max_frames=50)
    
    print("\n" + "="*60)
    print("✓ All tests completed!")
    print("="*60)


if __name__ == "__main__":
    main()
