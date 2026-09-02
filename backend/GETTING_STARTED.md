# Getting Started Guide

## Backend Architecture

This backend implements the complete surveillance system with:

1. **FastAPI** - Async Python web framework
2. **PostgreSQL** - Relational database for incidents and metadata
3. **Redis** - Real-time pub/sub and caching
4. **MinIO** - S3-compatible object storage for videos/snapshots
5. **MLflow** - Model registry and experiment tracking
6. **Celery** - Distributed task queue for training jobs
7. **YOLO v8** - Real-time object detection
8. **Re-ID** - Person re-identification across cameras

## Quick Start (3 Steps)

### Step 1: Start Services with Docker Compose
```bash
cd backend
docker-compose up -d
```

Wait ~30 seconds for services to initialize.

### Step 2: Initialize Database
```bash
docker-compose exec backend python -c "from app.db.database import init_db; init_db()"
```

### Step 3: Test the API
```bash
curl http://localhost:8000/docs  # Open in browser for interactive API docs
```

## Project Files Overview

### Core Files

**app/api/main.py**
- FastAPI application setup
- WebSocket connection manager for real-time alerts
- Redis listener for pub/sub
- Request/response handling

**app/db/models.py**
- SQLAlchemy ORM models:
  - `Incident` - Detected objects/alerts
  - `TrainJob` - Training job records
  - `Model` - Registered models
  - `Snapshot` - Saved frames with embeddings

**app/api/routes/incidents.py**
- `POST /incidents` - Create detection
- `GET /incidents` - List with filters
- `PATCH /incidents/{id}` - Verify/reject (human-in-loop)
- `GET /incidents/{id}/snapshots` - Get related snapshots

**app/api/routes/models.py**
- `POST /models/train` - Trigger training
- `GET /models/train/{id}` - Check training status
- `GET /models/production` - Get active model
- `POST /models/deploy` - Deploy new model

**app/ml/yolo_infer.py**
- YOLO v8 inference wrapper
- Frame processing and detection extraction

**app/ml/reid_embed.py**
- Person re-identification embedding service
- Cosine similarity matching
- Cross-camera person tracking

**app/workers/trainer_task.py**
- YOLO model training orchestration
- MLflow integration for logging
- Artifact storage in MinIO
- Training job status tracking

**app/services/storage.py**
- MinIO S3 client
- Snapshot saving
- Model artifact storage
- Presigned URL generation

**app/services/mlflow_client.py**
- MLflow experiment tracking
- Model registration
- Metrics and parameter logging

## API Examples

### 1. Send Detection
```bash
curl -X POST http://localhost:8000/api/v1/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "source_cam": "camera_1",
    "bbox": [640, 480, 100, 150],
    "snapshot_path": "s3://surveillance/snap.jpg",
    "confidence": 0.95,
    "track_id": "person_1"
  }'
```

### 2. List Pending Detections
```bash
curl http://localhost:8000/api/v1/incidents?status=pending&hours=24
```

### 3. Human Verification
```bash
curl -X PATCH http://localhost:8000/api/v1/incidents/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "verified"}'
```

### 4. Trigger Training Job
```bash
curl -X POST http://localhost:8000/api/v1/models/train \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "yolo_custom",
    "base_model": "yolov8m.pt",
    "epochs": 50,
    "batch_size": 16,
    "data_yaml_path": "/path/to/dataset.yaml"
  }'
```

### 5. Check Training Status
```bash
curl http://localhost:8000/api/v1/models/train/1
```

### 6. Deploy Model
```bash
curl -X POST http://localhost:8000/api/v1/models/deploy \
  -H "Content-Type: application/json" \
  -d '{"model_id": 5}'
```

### 7. WebSocket Real-Time Alerts
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/alerts');
ws.onmessage = (event) => {
  console.log('Alert:', JSON.parse(event.data));
};
```

## Service URLs

| Service | URL | Username | Password |
|---------|-----|----------|----------|
| FastAPI Docs | http://localhost:8000/docs | - | - |
| MinIO Console | http://localhost:9001 | minioadmin | minioadmin |
| MLflow UI | http://localhost:5000 | - | - |
| PostgreSQL | localhost:5432 | postgres | postgres_password |
| Redis | localhost:6379 | - | - |

## Integration with Frontend

Your React dashboard should:

1. Connect WebSocket to `/ws/alerts`
2. Display incoming incident alerts in real-time
3. Show snapshot images from MinIO
4. Call API endpoints to verify incidents
5. Show training progress from MLflow

Example React integration:
```javascript
// Connect to alerts
const ws = useEffect(() => {
  const socket = new WebSocket('ws://localhost:8000/ws/alerts');
  socket.onmessage = (event) => {
    const alert = JSON.parse(event.data);
    // Update incident display
    setIncidents(prev => [alert, ...prev]);
  };
}, []);

// Fetch incidents on load
useEffect(() => {
  fetch('/api/v1/incidents?status=pending')
    .then(r => r.json())
    .then(setIncidents);
}, []);

// Verify incident (human review)
const verifyIncident = (id) => {
  fetch(`/api/v1/incidents/${id}`, {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({status: 'verified'})
  });
};

// Trigger training
const triggerTraining = () => {
  fetch('/api/v1/models/train', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      model_name: 'yolo_custom',
      epochs: 50,
      data_yaml_path: '/data/dataset.yaml'
    })
  });
};
```

## Data Flow

```
Video/RTSP Stream
      ↓
Detection Worker (YOLO inference)
      ↓
Create Incident + Save Snapshot (MinIO)
      ↓
Publish to Redis → WebSocket Broadcast
      ↓
React Dashboard (Real-time alert)
      ↓
Human Reviews & Verifies
      ↓
Verified incidents → Training dataset
      ↓
Trigger Training → Celery Task
      ↓
Train YOLO → MLflow Logging
      ↓
Evaluate Model → Deploy if better
      ↓
Update Production Model
```

## Local Development (No Docker)

### Prerequisites
- Python 3.10+
- PostgreSQL running locally
- Redis running locally
- MinIO running (Docker)

### Setup
```bash
# Create venv
python -m venv venv
source venv/bin/activate

# Install deps
pip install -r requirements.txt

# Start infrastructure
docker-compose up postgres redis minio mlflow -d

# Run backend
uvicorn app.api.main:app --reload

# In another terminal: Run Celery
celery -A app.workers.celery_app worker --loglevel=info
```

## Key Configuration

**Settings** (app/core/config.py)
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection
- `MINIO_URL` - MinIO endpoint
- `MLFLOW_TRACKING_URI` - MLflow server

**Environment** (.env)
```
DATABASE_URL=postgresql://postgres:password@postgres:5432/db
REDIS_URL=redis://redis:6379/0
MINIO_URL=http://minio:9000
DEBUG=False
```

## Testing the System

### 1. Send Test Detection
```bash
python -c "
import requests
requests.post('http://localhost:8000/api/v1/incidents', json={
    'source_cam': 'test_cam',
    'bbox': [100, 100, 50, 50],
    'snapshot_path': 'test/snap.jpg',
    'confidence': 0.9
})
"
```

### 2. Check Database
```bash
docker-compose exec postgres psql -U postgres -d surveillance_db -c "SELECT * FROM incidents;"
```

### 3. Verify MinIO
```bash
docker-compose exec minio mc ls local/surveillance
```

### 4. Check MLflow
Open http://localhost:5000

### 5. Monitor Redis
```bash
docker-compose exec redis redis-cli MONITOR
```

## Debugging

### View Logs
```bash
# Backend
docker-compose logs -f backend

# Celery
docker-compose logs -f celery_worker

# All services
docker-compose logs -f
```

### Database Issues
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres

# List databases
\l

# Use surveillance_db
\c surveillance_db

# List tables
\dt
```

### Redis Issues
```bash
docker-compose exec redis redis-cli
PING
KEYS *
FLUSHDB
```

## Next Steps

1. **Build Detection Worker** - Integrate actual YOLO inference pipeline
2. **Build UI Dashboard** - React component to display alerts and verify incidents
3. **Prepare Dataset** - Collect and annotate training data
4. **Fine-tune Model** - Run training on custom dataset
5. **Deploy to Production** - Set up Kubernetes cluster

## Demo Checklist

- [ ] Start all services with Docker Compose
- [ ] Send test detection via API
- [ ] Verify incident appears in database
- [ ] Connect React app to WebSocket
- [ ] Receive real-time alerts
- [ ] Verify incident (human review)
- [ ] Trigger training job
- [ ] Watch MLflow track metrics
- [ ] Deploy new model
- [ ] Test inference with new model

---

For more details, see README.md
