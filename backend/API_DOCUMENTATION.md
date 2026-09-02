# Surveillance Backend - Complete API Documentation

**All available endpoints for the Sawdhan AI Surveillance Backend**

---

## 🌐 Base URL
```
http://localhost:8000
```

## 📚 API Documentation (Interactive)
```
http://localhost:8000/docs (Swagger UI)
http://localhost:8000/redoc (ReDoc)
```

---

## ✅ Health & Info Endpoints

### GET `/health`
Check if backend is running

**Response:**
```json
{
  "status": "ok"
}
```

### GET `/`
Get API information

**Response:**
```json
{
  "name": "Surveillance Backend",
  "version": "0.1.0",
  "api_base": "/api/v1"
}
```

---

## 🎬 Incident Management Endpoints

### POST `/api/v1/incidents`
Create a new incident

**Request Body:**
```json
{
  "source_cam": "camera_01",
  "bbox": {
    "x_min": 100,
    "y_min": 150,
    "x_max": 300,
    "y_max": 400
  },
  "snapshot_path": "/snapshots/incident_001.jpg",
  "confidence": 0.95,
  "track_id": 1,
  "meta": {
    "class": "person",
    "alert_type": "suspicious_movement"
  }
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "source_cam": "camera_01",
  "timestamp": "2026-09-01T10:30:00",
  "bbox": {...},
  "snapshot_path": "/snapshots/incident_001.jpg",
  "status": "pending",
  "confidence": 0.95,
  "track_id": 1,
  "meta": {...},
  "created_at": "2026-09-01T10:30:00"
}
```

### GET `/api/v1/incidents`
List incidents with filters

**Query Parameters:**
- `limit` (int, default=10): Max results
- `skip` (int, default=0): Pagination offset
- `status` (str): Filter by status (pending, reviewed, false_alarm, resolved)
- `source_cam` (str): Filter by camera ID
- `hours` (int, default=24): Last N hours

**Example:**
```
GET /api/v1/incidents?limit=50&status=pending&source_cam=camera_01&hours=24
```

**Response:**
```json
{
  "count": 5,
  "incidents": [
    {
      "id": 1,
      "source_cam": "camera_01",
      "timestamp": "2026-09-01T10:30:00",
      "status": "pending",
      "confidence": 0.95,
      ...
    }
  ]
}
```

### GET `/api/v1/incidents/{incident_id}`
Get specific incident details

**Response:**
```json
{
  "id": 1,
  "source_cam": "camera_01",
  "timestamp": "2026-09-01T10:30:00",
  "bbox": {...},
  "snapshot_path": "/snapshots/incident_001.jpg",
  "status": "pending",
  "confidence": 0.95,
  "track_id": 1,
  "meta": {...},
  "created_at": "2026-09-01T10:30:00"
}
```

### PATCH `/api/v1/incidents/{incident_id}`
Update incident status

**Request Body:**
```json
{
  "status": "reviewed",
  "meta": {
    "reviewer": "admin",
    "notes": "False alarm - no actual threat"
  }
}
```

**Response:**
```json
{
  "id": 1,
  "status": "reviewed",
  "meta": {...}
}
```

### GET `/api/v1/incidents/{incident_id}/snapshots`
Get all snapshots for an incident

**Response:**
```json
{
  "incident_id": 1,
  "snapshots": [
    {
      "id": 1,
      "incident_id": 1,
      "minio_key": "incidents/incident_001/snapshot_0.jpg",
      "embedding": [0.1, 0.2, 0.3, ...],
      "created_at": "2026-09-01T10:30:00"
    }
  ]
}
```

---

## 🤖 Model Management Endpoints

### GET `/api/v1/models`
List all trained models

**Query Parameters:**
- `status` (str): Filter by status (training, deployed, archived)

**Response:**
```json
[
  {
    "id": 1,
    "model_name": "person_detector_v2",
    "version": "2.0",
    "base_model": "yolov8n",
    "status": "deployed",
    "metrics": {
      "mAP": 0.85,
      "precision": 0.90,
      "recall": 0.82
    },
    "created_at": "2026-08-01T10:30:00"
  }
]
```

### GET `/api/v1/models/production`
Get current production model

**Response:**
```json
{
  "id": 1,
  "model_name": "person_detector_v2",
  "version": "2.0",
  "base_model": "yolov8n",
  "status": "deployed",
  ...
}
```

### POST `/api/v1/models/train`
Trigger manual training job (traditional method)

**Request Body:**
```json
{
  "model_name": "custom_detector",
  "base_model": "yolov8m",
  "epochs": 50,
  "batch_size": 16,
  "data_yaml_path": "/path/to/dataset/data.yaml"
}
```

**Response (202 Accepted):**
```json
{
  "id": 1,
  "status": "queued",
  "config": {...},
  "created_at": "2026-09-01T10:30:00",
  "started_at": null,
  "completed_at": null,
  "result": null
}
```

### GET `/api/v1/models/train`
List all training jobs

**Query Parameters:**
- `skip` (int, default=0): Pagination
- `limit` (int, default=50): Max results
- `status` (str): Filter by status

**Response:**
```json
[
  {
    "id": 1,
    "status": "running",
    "config": {...},
    "created_at": "2026-09-01T10:30:00",
    "started_at": "2026-09-01T10:31:00",
    "completed_at": null,
    "result": null
  }
]
```

### GET `/api/v1/models/train/{job_id}`
Get specific training job status

**Response:**
```json
{
  "id": 1,
  "status": "completed",
  "config": {...},
  "created_at": "2026-09-01T10:30:00",
  "started_at": "2026-09-01T10:31:00",
  "completed_at": "2026-09-01T11:45:00",
  "result": {
    "best_epoch": 35,
    "final_map": 0.87,
    "model_path": "/models/detector_v2.pt"
  }
}
```

### GET `/api/v1/models/train/{job_id}/logs`
Get training logs for a job

**Response:**
```json
{
  "logs": "Epoch 1/50: loss=0.45, map=0.23...\nEpoch 2/50: loss=0.42, map=0.25...\n..."
}
```

### POST `/api/v1/models/deploy`
Deploy a model to production

**Request Body:**
```json
{
  "model_id": 1
}
```

**Response:**
```json
{
  "id": 1,
  "model_name": "person_detector_v2",
  "status": "deployed",
  ...
}
```

---

## ⚡ Auto-Train Pipeline Endpoints (NEW!)

### POST `/api/v1/models/auto-train`
**1-Click Automated YOLO Training from Video**

Extracts frames, auto-labels using YOLO-World, trains YOLOv8n, runs inference. No manual labeling required!

**Request Body:**
```json
{
  "video_path": "/path/to/video.mp4",
  "classes": ["person", "motorcycle", "weapon", "helmet"],
  "epochs": 15,
  "frame_interval": 4
}
```

**Response (202 Accepted):**
```json
{
  "job_id": "a1b2c3d4",
  "status": "queued",
  "message": "Training job submitted. Use job_id to check status.",
  "created_at": "2026-09-01T10:30:00"
}
```

**Status Codes:**
- `202`: Job submitted successfully
- `400`: Invalid video path or parameters
- `422`: Validation error in request body

### GET `/api/v1/models/auto-train/status/{job_id}`
**Check Auto-Train Job Progress**

**Example:**
```
GET /api/v1/models/auto-train/status/a1b2c3d4
```

**Response:**
```json
{
  "job_id": "a1b2c3d4",
  "status": "running",
  "progress": 45,
  "message": "Training model (epoch 7/15)...",
  "created_at": "2026-09-01T10:30:00",
  "started_at": "2026-09-01T10:31:00",
  "completed_at": null,
  "results": null,
  "error": null
}
```

**Status Values:**
- `pending`: Waiting to start
- `running`: Currently processing
- `completed`: Successfully finished
- `failed`: Error occurred

**Progress Field:**
- 0-20%: Extracting and labeling frames
- 20-80%: Training model
- 80-100%: Running inference
- 100%: Complete

### GET `/api/v1/models/auto-train/download/{job_id}`
**Download Trained Model and Results**

Available after job is completed.

**Response:**
```json
{
  "job_id": "a1b2c3d4",
  "status": "completed",
  "model_path": "auto_train_output/a1b2c3d4/models/trained_model/weights/best.pt",
  "output_video": "auto_train_output/a1b2c3d4/inference/output_annotated.mp4",
  "dataset_path": "auto_train_output/a1b2c3d4/dataset",
  "frames_extracted": 180,
  "detections_count": 3421
}
```

**Status Codes:**
- `200`: Results available
- `404`: Job not found
- `400`: Job not completed yet

---

## 🔌 WebSocket Endpoint

### WebSocket `/ws/alerts`
Real-time incident alerts via WebSocket

**Connection:**
```
WS ws://localhost:8000/ws/alerts
```

**Message Format (incoming):**
```json
{
  "type": "incident_alert",
  "incident_id": 1,
  "source_cam": "camera_01",
  "timestamp": "2026-09-01T10:30:00",
  "confidence": 0.95,
  "message": "Suspicious object detected on camera_01"
}
```

**Example (JavaScript):**
```javascript
const ws = new WebSocket("ws://localhost:8000/ws/alerts");

ws.onmessage = (event) => {
  const alert = JSON.parse(event.data);
  console.log(`Alert from ${alert.source_cam}:`, alert.message);
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};
```

---

## 📊 Complete Workflow Example

### 1. Upload Video and Start Training
```bash
curl -X POST http://localhost:8000/api/v1/models/auto-train \
  -H "Content-Type: application/json" \
  -d '{
    "video_path": "/videos/surveillance.mp4",
    "classes": ["person", "weapon"],
    "epochs": 15
  }'
```

**Response:** `{"job_id": "xyz123", ...}`

### 2. Check Training Progress
```bash
curl http://localhost:8000/api/v1/models/auto-train/status/xyz123
```

### 3. Download Results (when completed)
```bash
curl http://localhost:8000/api/v1/models/auto-train/download/xyz123
```

### 4. Use Model for Detection
```python
from ultralytics import YOLO

model = YOLO("auto_train_output/xyz123/models/trained_model/weights/best.pt")
results = model("test_image.jpg")
```

---

## 🔄 Background Task Management

All long-running operations (training, detection) run in background:

- **Backend returns immediately** with job ID (202 Accepted)
- **Client polls status** via GET endpoint
- **Jobs persist** in `auto_train_output/{job_id}/job_info.json`
- **Results available** after job completes

---

## 🚨 Error Responses

### 400 Bad Request
```json
{
  "detail": "Video file not found: /path/to/nonexistent.mp4"
}
```

### 404 Not Found
```json
{
  "detail": "Job not found: invalid_job_id"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "epochs"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## 📋 Request/Response Standards

All requests with JSON body require:
```
Content-Type: application/json
```

All responses include:
- HTTP status code
- JSON body with appropriate fields
- `X-Request-ID` header (for tracing)

---

## 🔐 Authentication (Future)

Currently no authentication. Production should implement:
- JWT bearer tokens
- API keys
- Rate limiting

---

## 📊 Performance Metrics

| Endpoint | Avg Response Time | Notes |
|----------|------------------|-------|
| GET `/health` | <1ms | Always fast |
| GET `/api/v1/incidents?limit=10` | 10-50ms | Database query |
| POST `/api/v1/models/auto-train` | 100-500ms | Validation + job creation |
| GET `/api/v1/models/auto-train/status/{id}` | <50ms | File read |
| WebSocket `/ws/alerts` | <10ms | Per message |

---

## 🧪 Testing Endpoints

### Using Curl
```bash
# Health check
curl http://localhost:8000/health

# Create incident
curl -X POST http://localhost:8000/api/v1/incidents \
  -H "Content-Type: application/json" \
  -d '{"source_cam":"camera_01","bbox":{},"snapshot_path":"/test.jpg","confidence":0.9,"track_id":1}'

# List incidents
curl "http://localhost:8000/api/v1/incidents?limit=10"
```

### Using Python
```python
import requests

response = requests.get("http://localhost:8000/health")
print(response.json())

response = requests.post(
    "http://localhost:8000/api/v1/incidents",
    json={
        "source_cam": "camera_01",
        "bbox": {"x_min": 0, "y_min": 0, "x_max": 100, "y_max": 100},
        "snapshot_path": "/test.jpg",
        "confidence": 0.9,
        "track_id": 1
    }
)
print(response.json())
```

### Using Swagger UI
1. Open http://localhost:8000/docs
2. Click "Try it out" on any endpoint
3. Fill in parameters
4. Click "Execute"

---

## 🔄 Polling Pattern for Long-Running Tasks

```python
import requests
import time

# Submit job
response = requests.post(
    "http://localhost:8000/api/v1/models/auto-train",
    json={"video_path": "test.mp4", "classes": ["person"], "epochs": 15}
)
job_id = response.json()["job_id"]

# Poll until completion
max_wait = 3600  # 1 hour
poll_interval = 10  # seconds

elapsed = 0
while elapsed < max_wait:
    status = requests.get(
        f"http://localhost:8000/api/v1/models/auto-train/status/{job_id}"
    ).json()
    
    if status["status"] == "completed":
        print("Success!", status["results"])
        break
    elif status["status"] == "failed":
        print("Failed:", status["error"])
        break
    
    print(f"Progress: {status['progress']}%")
    time.sleep(poll_interval)
    elapsed += poll_interval
```

---

**🎉 Complete API Reference for Sawdhan AI Surveillance Backend**

All endpoints ready for integration with frontend or external systems!
