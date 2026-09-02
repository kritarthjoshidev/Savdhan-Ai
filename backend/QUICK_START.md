# 🚀 Surveillance Backend - Quick Start Guide

## ✅ Current Status

Your surveillance backend is **RUNNING and FULLY OPERATIONAL**!

**Server Details:**
- 🌐 **API Base:** http://localhost:8000
- 📚 **Interactive Docs:** http://localhost:8000/docs  
- 🔗 **WebSocket Alerts:** ws://localhost:8000/ws/alerts
- ✅ **Health Check:** http://localhost:8000/health

---

## 📋 Quick Access

### API Endpoints Ready to Use

**Incidents Management:**
- `GET /api/v1/incidents` - List all incidents
- `POST /api/v1/incidents` - Create new incident
- `GET /api/v1/incidents/{id}` - Get specific incident
- `PATCH /api/v1/incidents/{id}` - Update incident status
- `GET /api/v1/incidents/{id}/snapshots` - Get snapshots for incident

**Models & Training:**
- `GET /api/v1/models` - List trained models
- `POST /api/v1/models/train` - Start training job
- `GET /api/v1/models/train/{id}` - Get training job status
- `POST /api/v1/models/deploy` - Deploy model to production

---

## 🛠️ How to Keep Backend Running

### Option 1: Batch File (Windows - Recommended)
```bash
# Double-click to start
run_backend.bat
```

### Option 2: PowerShell Script
```powershell
# Run in PowerShell
.\run_backend.ps1
```

### Option 3: Direct Python
```bash
cd "c:\Users\krita\Downloads\sawdhan ai\backend"
python run_backend.py
```

### Option 4: Uvicorn CLI
```bash
cd "c:\Users\krita\Downloads\sawdhan ai\backend"
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🧪 Testing the API

### Using Python
```python
import requests

# Test health
r = requests.get("http://localhost:8000/health")
print(r.json())  # {"status": "ok"}

# List incidents
r = requests.get("http://localhost:8000/api/v1/incidents")
print(r.json())

# Create incident
payload = {
    "source_cam": "camera_01",
    "bbox": [640, 480, 100, 150],
    "snapshot_path": "s3://surveillance/snapshots/frame_001.jpg",
    "confidence": 0.95,
    "meta": {"event_type": "intrusion"}
}
r = requests.post("http://localhost:8000/api/v1/incidents", json=payload)
print(r.json())
```

### Using Interactive Docs
Open http://localhost:8000/docs in your browser to use Swagger UI:
- 📝 View all endpoints
- 🧪 Test requests directly
- 📖 Read API documentation
- ⬇️ Try it out without writing code

---

## 🗂️ Project Structure

```
backend/
├── app/
│   ├── api/              # FastAPI routes & WebSocket
│   │   └── routes/       # Incident & Model endpoints
│   ├── db/               # Database models & CRUD
│   ├── core/             # Configuration & events
│   ├── ml/               # YOLO inference & Re-ID
│   ├── services/         # MinIO, MLflow clients
│   └── workers/          # Celery tasks & training
├── requirements.txt      # Python dependencies
├── run_backend.py        # Startup script
├── run_backend.bat       # Windows batch launcher
├── run_backend.ps1       # PowerShell launcher
└── docker-compose.yml    # Full deployment (optional)
```

---

## 💾 Database

**Default:** SQLite (local, no Docker needed)
- 📁 File: `surveillance.db`
- Auto-creates on startup
- No setup required!

**Alternative:** PostgreSQL (requires Docker)
```bash
# Set environment variable
$env:USE_POSTGRES = "1"

# Then start backend
python run_backend.py
```

---

## 🔗 Integration with Frontend

Your backend is ready for React frontend integration:

```javascript
// React example
const API_URL = "http://localhost:8000";

// Fetch incidents
fetch(`${API_URL}/api/v1/incidents`)
  .then(r => r.json())
  .then(data => console.log(data));

// Create incident
fetch(`${API_URL}/api/v1/incidents`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    source_cam: "camera_01",
    bbox: [640, 480, 100, 150],
    snapshot_path: "s3://...",
    confidence: 0.95,
    meta: {}
  })
})
.then(r => r.json())
.then(data => console.log(data));

// WebSocket for real-time alerts
const ws = new WebSocket("ws://localhost:8000/ws/alerts");
ws.onmessage = (event) => {
  const alert = JSON.parse(event.data);
  console.log("New alert:", alert);
};
```

---

## 📦 Installed Packages

Core dependencies successfully installed:
- ✅ FastAPI (0.141.1) - Web framework
- ✅ SQLAlchemy (2.0.52) - Database ORM
- ✅ Pydantic (2.13.5) - Data validation
- ✅ Uvicorn (0.52.4) - ASGI server
- ✅ Redis (8.1.0) - Pub/sub for alerts
- ✅ Ultralytics (8.0+) - YOLO v8 detection
- ✅ MLflow (3.15.2) - Model registry
- ✅ Boto3 (1.43.83) - S3/MinIO storage
- ✅ Celery (5.6.3) - Async tasks
- ✅ Pytest (9.1.1) - Testing

---

## 🎯 Next Steps

1. **Keep Backend Running:** Use one of the startup methods above
2. **Integrate Frontend:** Connect your React app to `http://localhost:8000`
3. **Test Endpoints:** Visit http://localhost:8000/docs to explore API
4. **Start YOLO Detection:** POST to `/api/v1/models/train` to train models
5. **Monitor Alerts:** Connect WebSocket for real-time incident notifications

---

## 🆘 Troubleshooting

**Backend won't start?**
- Make sure port 8000 is free: `netstat -ano | findstr :8000`
- Check Python installed: `python --version` (need 3.10+)
- Reinstall deps: `pip install -r requirements.txt`

**Endpoints return 404?**
- Verify backend is running: http://localhost:8000/health should return 200
- Check API path: Use `/api/v1/` prefix
- Visit Swagger docs: http://localhost:8000/docs

**Database errors?**
- Default SQLite should auto-create
- Check file permissions in backend directory
- Data stored in `surveillance.db`

**Import errors?**
```bash
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

---

## 📞 Key Endpoints Summary

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/` | API info |
| GET | `/docs` | Interactive documentation |
| GET | `/api/v1/incidents` | List incidents |
| POST | `/api/v1/incidents` | Create incident |
| PATCH | `/api/v1/incidents/{id}` | Update incident |
| GET | `/api/v1/models` | List models |
| POST | `/api/v1/models/train` | Train new model |
| WS | `/ws/alerts` | WebSocket for real-time alerts |

---

**🎉 Your backend is ready! Start building!**
