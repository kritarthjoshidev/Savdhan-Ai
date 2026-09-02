# Surveillance Backend

Complete production-ready backend for video surveillance system with AI detection, tracking, and model training.

## Features

- **FastAPI** backend with async/await and WebSocket support
- **YOLO v8** integration for real-time object detection
- **Re-ID** (person re-identification) for cross-camera tracking
- **PostgreSQL** for structured data (incidents, models, training jobs)
- **MinIO** S3-compatible object storage for videos and snapshots
- **Redis** pub/sub for real-time event streaming
- **MLflow** for model versioning and experiment tracking
- **Celery** for async training and heavy computation tasks
- **Docker Compose** for easy deployment

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── main.py           # FastAPI app, WebSocket endpoints
│   │   └── routes/
│   │       ├── incidents.py  # Incident detection & verification API
│   │       └── models.py     # Model management & training trigger API
│   ├── core/
│   │   ├── config.py         # Configuration & settings
│   │   └── events.py         # Redis pub/sub helpers
│   ├── db/
│   │   ├── models.py         # SQLAlchemy ORM models
│   │   ├── crud.py           # Database operations
│   │   └── database.py       # DB connection & session
│   ├── ml/
│   │   ├── yolo_infer.py    # YOLO inference wrapper
│   │   └── reid_embed.py    # Re-ID embedding service
│   ├── services/
│   │   ├── storage.py        # MinIO S3 client
│   │   └── mlflow_client.py # MLflow tracking client
│   └── workers/
│       ├── detection_worker.py  # YOLO detection processing
│       ├── tracker_worker.py    # Multi-object tracking & matching
│       ├── trainer_task.py      # YOLO training orchestration
│       └── celery_app.py        # Celery configuration
├── docker-compose.yml  # Full stack orchestration
├── Dockerfile          # Backend container
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
└── README.md          # This file
```

## Quick Start (Docker)

### 1. Clone the repo and setup

```bash
cd backend
cp .env.example .env
```

### 2. Start all services

```bash
docker-compose up -d
```

This starts:
- **PostgreSQL** on port 5432
- **Redis** on port 6379
- **MinIO** on port 9000 (UI: 9001)
- **MLflow** on port 5000
- **FastAPI Backend** on port 8000
- **Celery Worker** & **Celery Beat** for async tasks

### 3. Access services

- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- MinIO Console: http://localhost:9001
- MLflow UI: http://localhost:5000
- Redis: localhost:6379

### 4. Initialize database

```bash
docker-compose exec backend python -c "from app.db.database import init_db; init_db()"
```

## API Endpoints

### Incidents (Detection Results)

```
POST   /api/v1/incidents           # Create incident
GET    /api/v1/incidents           # List incidents (with filters)
GET    /api/v1/incidents/{id}      # Get specific incident
PATCH  /api/v1/incidents/{id}      # Verify/reject (human-in-loop)
GET    /api/v1/incidents/{id}/snapshots  # Get snapshots for incident
```

### Models (Training & Serving)

```
GET    /api/v1/models              # List models
GET    /api/v1/models/production   # Get active production model
POST   /api/v1/models/train        # Trigger training job
GET    /api/v1/models/train        # List training jobs
GET    /api/v1/models/train/{id}   # Get training job status
POST   /api/v1/models/deploy       # Deploy model to production
GET    /api/v1/models/train/{id}/logs  # Get training logs
```

### WebSocket

```
WS     /ws/alerts                  # Real-time incident notifications
```

## Usage Examples

### 1. Detect objects in video

```bash
curl -X POST http://localhost:8000/api/v1/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "source_cam": "cam_01",
    "bbox": [100, 150, 50, 80],
    "snapshot_path": "snapshots/cam_01/frame_001.jpg",
    "confidence": 0.92,
    "meta": {"track_id": "track_123"}
  }'
```

### 2. List detections

```bash
curl http://localhost:8000/api/v1/incidents?status=pending&hours=24
```

### 3. Verify incident (human review)

```bash
curl -X PATCH http://localhost:8000/api/v1/incidents/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "verified", "meta": {"reviewer": "admin"}}'
```

### 4. Trigger model training

```bash
curl -X POST http://localhost:8000/api/v1/models/train \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "yolo_v8_person",
    "base_model": "yolov8m.pt",
    "epochs": 50,
    "batch_size": 16,
    "data_yaml_path": "/data/training/dataset.yaml"
  }'
```

### 5. Check training progress

```bash
curl http://localhost:8000/api/v1/models/train/1
curl http://localhost:8000/api/v1/models/train/1/logs
```

### 6. Deploy trained model

```bash
curl -X POST http://localhost:8000/api/v1/models/deploy \
  -H "Content-Type: application/json" \
  -d '{"model_id": 5}'
```

### 7. Connect WebSocket for real-time alerts

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/alerts');
ws.onmessage = (event) => {
  const alert = JSON.parse(event.data);
  console.log('New incident:', alert);
  // Update dashboard, show snapshot, etc.
};
```

## Training Data Preparation

### YOLO Dataset Format

Create a `dataset.yaml`:

```yaml
path: /path/to/dataset
train: images/train
val: images/val
test: images/test

nc: 1  # number of classes
names: ['person']  # class names
```

Dataset structure:
```
dataset/
├── images/
│   ├── train/  (1000+ images)
│   ├── val/    (200+ images)
│   └── test/   (100+ images)
└── labels/     (YOLO format .txt files)
```

### Quick Training

Once MLflow is running:

```bash
docker-compose exec backend python -c "
from app.workers.trainer_task import train_yolo_task
train_yolo_task(job_id=1, config={
    'base_model': 'yolov8n.pt',
    'epochs': 50,
    'batch_size': 16,
    'data_yaml_path': '/data/dataset.yaml'
})
"
```

## Local Development (without Docker)

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Update .env with your local services
```

### Run services locally

**Terminal 1 - FastAPI**:
```bash
uvicorn app.api.main:app --reload --port 8000
```

**Terminal 2 - Celery Worker** (optional):
```bash
celery -A app.workers.celery_app worker --loglevel=info
```

You still need PostgreSQL, Redis, and MinIO running (use Docker for these):

```bash
# Just the infrastructure services
docker-compose up postgres redis minio mlflow -d
```

## Configuration

Edit `.env` to customize:

- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `MINIO_URL` - MinIO endpoint
- `MLFLOW_TRACKING_URI` - MLflow server
- `DEBUG` - Enable/disable debug mode

## Key Classes & Functions

### Detection
```python
from app.ml.yolo_infer import YOLOInference
yolo = YOLOInference("yolov8n.pt")
detections = yolo.process_frame(frame)
```

### Re-ID Matching
```python
from app.ml.reid_embed import ReIDEmbedding
reid = ReIDEmbedding()
embedding = reid.get_embedding(person_crop)
similarity = reid.compute_similarity(emb1, emb2)
```

### Storage
```python
from app.services.storage import get_storage
storage = get_storage()
key = storage.save_snapshot("cam_01", frame, [100,150,50,80])
url = storage.get_object_url(key)
```

### Database
```python
from app.db.database import SessionLocal
from app.db import crud
db = SessionLocal()
incidents = crud.list_incidents(db, status="pending")
```

## Deployment Considerations

### Production Checklist

- [ ] Set `DEBUG=False` in .env
- [ ] Use strong PostgreSQL password
- [ ] Configure MinIO auth properly
- [ ] Enable HTTPS on API endpoints
- [ ] Set up logging & monitoring (Prometheus, ELK)
- [ ] Configure database backups
- [ ] Use Kubernetes for scaling
- [ ] Add authentication/authorization to API
- [ ] Rate limiting on endpoints
- [ ] Model versioning strategy in MLflow

### Scaling

For production, use Kubernetes:

```bash
# Build and push images
docker build -t myregistry/surveillance-backend .
docker push myregistry/surveillance-backend

# Deploy with Helm or kubectl
kubectl apply -f k8s/
```

## Troubleshooting

### Services won't start
```bash
docker-compose logs -f <service_name>
```

### Database connection error
```bash
docker-compose exec postgres psql -U postgres -c "\l"
```

### MinIO not accessible
```bash
docker-compose exec minio mc admin info local
```

### Training job stuck
```bash
docker-compose logs -f celery_worker
```

## Contributing

1. Fork the repo
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

MIT
