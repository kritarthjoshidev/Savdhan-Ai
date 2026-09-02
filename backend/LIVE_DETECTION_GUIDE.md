# 📹 Live Detection Guide - Webcam + CCTV (RTSP)

## اردو میں خوش آمدید! 🇵🇰

یہ گائیڈ آپ کو **Live CCTV اور Webcam detection** کے ساتھ شروع کرنے میں مدد دے گی۔

---

## Quick Start - 3 طریقے

### 1️⃣ **Webcam سے Detection** (سب سے آسان)

```bash
# ✓ Terminal میں چلائیں
curl -X POST "http://localhost:8000/api/v1/live/webcam/detect" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": 0,
    "conf_threshold": 0.5,
    "max_frames": 100
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Webcam detection completed",
  "stats": {
    "frames_processed": 100,
    "total_detections": 45,
    "classes_detected": ["person", "car", "bicycle"],
    "avg_detections_per_frame": 0.45
  }
}
```

---

### 2️⃣ **RTSP Stream سے Detection** (CCTV)

```bash
# ✓ اپنا RTSP URL لگائیں
curl -X POST "http://localhost:8000/api/v1/live/rtsp/detect" \
  -H "Content-Type: application/json" \
  -d '{
    "rtsp_url": "rtsp://admin:password@192.168.1.100:554/stream",
    "conf_threshold": 0.5,
    "max_frames": 500
  }'
```

**RTSP URL Examples:**
```
# Hikvision CCTV
rtsp://admin:password@192.168.1.100:554/h264/ch1/main/av_stream

# Dahua CCTV
rtsp://admin:password@192.168.1.100:554/stream/main

# Generic IP Camera
rtsp://admin:password@ip_address:554/path

# Online Test Stream (testing کے لیے)
rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mov
```

---

### 3️⃣ **WebSocket سے Real-Time Streaming**

```javascript
// HTML/JavaScript میں

// Webcam stream
const ws = new WebSocket('ws://localhost:8000/api/v1/live/webcam/stream?device_id=0');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'stream_info') {
    console.log(`Connected: ${data.resolution} @ ${data.fps}fps`);
  }
  
  if (data.type === 'detection') {
    console.log(`Frame ${data.frame}: ${data.detection_count} detections`);
    data.detections.forEach(det => {
      console.log(`  - ${det.class}: ${det.confidence}`);
    });
  }
  
  if (data.type === 'stream_end') {
    console.log('Stream ended');
  }
};

ws.onerror = (error) => console.error('WebSocket error:', error);
```

---

## API Endpoints تفصیل سے

### 📷 Webcam Endpoints

#### 1. Check Webcam Available
```
GET /api/v1/live/webcam/available?device_id=0
```

**Response:**
```json
{
  "status": "available",
  "device_id": 0,
  "resolution": "1920x1080",
  "fps": 30
}
```

---

#### 2. Webcam Detection
```
POST /api/v1/live/webcam/detect
```

**Request Body:**
```json
{
  "device_id": 0,                    // Webcam device ID (0 = default)
  "conf_threshold": 0.5,             // Confidence threshold (0-1)
  "max_frames": 100,                 // Max frames (null = infinite)
  "stream_fps": 30                   // Target FPS for streaming
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Webcam detection completed",
  "stats": {
    "frames_processed": 100,
    "total_detections": 50,
    "classes_detected": ["person", "car"],
    "avg_detections_per_frame": 0.5
  }
}
```

---

#### 3. Webcam WebSocket Stream
```
WS /api/v1/live/webcam/stream?device_id=0
```

**Messages Received:**

1. **Stream Info** (جڑنے پر):
```json
{
  "type": "stream_info",
  "resolution": "640x480",
  "fps": 30,
  "status": "streaming"
}
```

2. **Detection Data** (ہر فریم):
```json
{
  "type": "detection",
  "frame": 125,
  "detections": [
    {
      "class": "person",
      "confidence": 0.95,
      "bbox": [100.5, 150.2, 300.8, 450.1]
    }
  ],
  "detection_count": 1
}
```

3. **Stream End** (ختم ہونے پر):
```json
{
  "type": "stream_end",
  "frames_processed": 500,
  "total_detections": 250
}
```

---

### 📹 RTSP Endpoints (CCTV)

#### 1. Test RTSP Connection
```
POST /api/v1/live/rtsp/test?rtsp_url=rtsp://...
```

**Response:**
```json
{
  "status": "connected",
  "rtsp_url": "rtsp://admin:password@192.168.1.1...",
  "resolution": "1920x1080",
  "fps": 30,
  "message": "RTSP stream is accessible"
}
```

---

#### 2. RTSP Detection
```
POST /api/v1/live/rtsp/detect
```

**Request Body:**
```json
{
  "rtsp_url": "rtsp://admin:password@192.168.1.100:554/stream",
  "conf_threshold": 0.5,
  "max_frames": 1000,
  "stream_fps": 30
}
```

**Response:** (Webcam جیسے)

---

#### 3. RTSP WebSocket Stream
```
WS /api/v1/live/rtsp/stream?rtsp_url=rtsp://...
```

**Messages:** (Webcam جیسے)

---

### 🎬 Video File Endpoints

#### 1. Video File Detection
```
POST /api/v1/live/video/detect
```

**Request Body:**
```json
{
  "video_path": "./test_video.mp4",
  "conf_threshold": 0.5,
  "max_frames": null
}
```

**Response:** (Webcam جیسے)

---

## Real-World Examples 🌍

### مثال 1: اپنے CCTV سے Detection شروع کریں

```bash
#!/bin/bash

# آپنے CCTV کو ٹیسٹ کریں
RTSP_URL="rtsp://admin:admin123@192.168.1.10:554/stream1"

echo "🔍 Testing RTSP connection..."
curl -X POST "http://localhost:8000/api/v1/live/rtsp/test" \
  -H "Content-Type: application/json" \
  -d "{\"rtsp_url\": \"$RTSP_URL\"}"

echo -e "\n✓ اب detection شروع کریں..."
curl -X POST "http://localhost:8000/api/v1/live/rtsp/detect" \
  -H "Content-Type: application/json" \
  -d "{
    \"rtsp_url\": \"$RTSP_URL\",
    \"conf_threshold\": 0.5,
    \"max_frames\": 500
  }"
```

---

### مثال 2: Webcam سے صرف "Person" Detect کریں

```python
import requests
import json

url = "http://localhost:8000/api/v1/live/webcam/detect"

payload = {
    "device_id": 0,
    "conf_threshold": 0.6,  # صرف high confidence
    "max_frames": 200       # 200 frames
}

response = requests.post(url, json=payload)
result = response.json()

print(f"Frames processed: {result['stats']['frames_processed']}")
print(f"Total detections: {result['stats']['total_detections']}")
print(f"Classes found: {result['stats']['classes_detected']}")
```

---

### مثال 3: WebSocket سے Real-Time Monitoring

```python
import asyncio
import websockets
import json

async def monitor_webcam():
    uri = "ws://localhost:8000/api/v1/live/webcam/stream?device_id=0"
    
    async with websockets.connect(uri) as websocket:
        while True:
            msg = await websocket.recv()
            data = json.loads(msg)
            
            if data.get('type') == 'detection':
                for det in data.get('detections', []):
                    print(f"🎯 {det['class']}: {det['confidence']:.2f}")
            
            if data.get('type') == 'stream_end':
                break

asyncio.run(monitor_webcam())
```

---

## Common Issues & Solutions 🔧

### Issue 1: Webcam نہیں ملا

```bash
# اپنا device ID تلاش کریں
# Linux:
ls /dev/video*

# Windows: Device manager میں دیکھیں
# MacOS:
python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"
```

---

### Issue 2: RTSP Connection Timeout

```bash
# RTSP URL test کریں ffmpeg سے:
ffmpeg -rtsp_transport tcp -i "rtsp://user:pass@ip:port/path" -t 5 -f null -

# یا VLC میں کھولیں:
vlc rtsp://user:pass@ip:port/path
```

---

### Issue 3: سست Performance

```json
// Solution: Confidence threshold بڑھائیں
{
  "conf_threshold": 0.7,    // 0.5 سے 0.7 (سست detections کو filter کریں)
  "max_frames": 300         // کم frames لیں
}
```

---

## GPU Status Check

```bash
# Check اگر GPU CUDA کے ساتھ ہے
python -c "import torch; print(torch.cuda.is_available())"

# اگر True ہے تو training fast ہوگی! 🚀
```

---

## Testing Script

```bash
cd backend
python test_live_detection.py
```

---

## Integration with Auto-Train Pipeline

Live detection کو Auto-Train کے ساتھ combine کریں:

```python
# 1. Webcam سے detection کریں
result = detector.detect_from_webcam(max_frames=100)

# 2. اگر detections ہوں تو auto-train شروع کریں
if result['stats']['total_detections'] > 50:
    # Auto-train API call
    requests.post("/api/v1/models/auto-train", json={
        "video_path": "webcam_recording.mp4",
        "target_classes": result['stats']['classes_detected']
    })
```

---

## Performance Tips ⚡

| Setting | Fast Performance | Accuracy |
|---------|------------------|----------|
| conf_threshold | 0.7 | 0.3-0.4 |
| imgsz | 416 | 640 |
| max_frames | 300 | None |
| Device | GPU (0) | 'cpu' |

---

## Architecture 🏗️

```
┌─────────────────┐
│ Webcam / CCTV   │
│  (Live Stream)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ FastAPI Live Detection Service      │
│                                     │
│  ├─ /webcam/detect (HTTP)          │
│  ├─ /rtsp/detect (HTTP)            │
│  ├─ /webcam/stream (WebSocket)     │
│  └─ /rtsp/stream (WebSocket)       │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ LiveDetector Service                │
│                                     │
│  ├─ detect_from_webcam()           │
│  ├─ detect_from_rtsp()             │
│  └─ detect_from_file()             │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ YOLO Model Inference                │
│ (yolov8n.pt)                        │
│                                     │
│ GPU/CPU Auto-Detected ✓             │
└─────────────────────────────────────┘
```

---

## GPU Acceleration 🚀

اب GPU auto-detect ہو رہی ہے!

```python
# Auto-detection کام کر رہی ہے:
from auto_train import get_device

device = get_device()
# Returns: 0 (GPU) یا 'cpu' (CPU)

print(device)  # 0 اگر GPU ہے, 'cpu' اگر نہیں
```

---

## اگلے قدم:

1. ✅ Webcam سے test کریں
2. ✅ RTSP stream add کریں
3. ✅ WebSocket سے monitoring کریں
4. ✅ Auto-train کے ساتھ integrate کریں

Happy Detecting! 🎯

---

**Support:** اگر کوئی سوال ہو تو پوچھیں! 🤝
