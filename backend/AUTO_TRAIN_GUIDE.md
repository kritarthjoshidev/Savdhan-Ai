# 🎯 Auto-Train Pipeline - Complete Guide

**1-Click Automated YOLO Training from Video**

No manual labeling required! Upload a video → Get a trained model.

---

## ⚡ Quick Start (30 seconds)

### Option 1: Direct Command (Simplest)

```bash
cd "c:\Users\krita\Downloads\sawdhan ai\backend"
python auto_train.py --video sample.mp4 --classes person,motorcycle --epochs 15
```

### Option 2: Via API (Recommended)

```bash
# 1. Start backend
python run_backend.py

# 2. In another terminal, submit training job
curl -X POST http://localhost:8000/api/v1/models/auto-train \
  -H "Content-Type: application/json" \
  -d '{
    "video_path": "sample.mp4",
    "classes": ["person", "motorcycle", "weapon"],
    "epochs": 15,
    "frame_interval": 4
  }'
```

### Option 3: Python Demo

```bash
python auto_train_demo.py --demo all --video sample.mp4
```

---

## 📊 How It Works

### Step 1: Frame Extraction & Auto-Labeling
- Video se frames extract hote hain
- **YOLO-World (yolov8s-world.pt)** se zero-shot detection
- Manual labeling की जरूरत नहीं! 🎉

### Step 2: Dataset Generation
- Frames को organized करो
- `.txt` label files auto-generate
- `data.yaml` prepare karo

### Step 3: Model Training
- **YOLOv8n** ko fine-tune karo
- Custom dataset par train karo
- Best weights save hote hain

### Step 4: Inference & Visualization
- Original video par trained model run karo
- Bounding boxes के साथ output video
- Detections की summary

---

## 🔧 Available Endpoints

### 1. POST `/api/v1/models/auto-train`
**Submit video for training**

```json
{
  "video_path": "sample.mp4",
  "classes": ["person", "motorcycle", "weapon", "helmet"],
  "epochs": 15,
  "frame_interval": 4
}
```

**Response:**
```json
{
  "job_id": "abc12345",
  "status": "queued",
  "message": "Training job submitted...",
  "created_at": "2026-09-01T10:30:00"
}
```

### 2. GET `/api/v1/models/auto-train/status/{job_id}`
**Check training progress**

**Response:**
```json
{
  "job_id": "abc12345",
  "status": "running",
  "progress": 45,
  "message": "Training model...",
  "created_at": "2026-09-01T10:30:00",
  "started_at": "2026-09-01T10:31:00",
  "results": null
}
```

**Status values:** `pending` → `running` → `completed` (or `failed`)

### 3. GET `/api/v1/models/auto-train/download/{job_id}`
**Download trained model and results**

**Response:**
```json
{
  "job_id": "abc12345",
  "status": "completed",
  "model_path": "auto_train_output/abc12345/models/trained_model/weights/best.pt",
  "output_video": "auto_train_output/abc12345/inference/output_annotated.mp4",
  "dataset_path": "auto_train_output/abc12345/dataset",
  "frames_extracted": 150,
  "detections_count": 2345
}
```

---

## 📁 Output Directory Structure

```
auto_train_output/
├── {job_id}/
│   ├── dataset/
│   │   ├── images/train/          # Extracted frames
│   │   ├── labels/train/          # Auto-generated .txt files
│   │   └── data.yaml              # YOLO dataset config
│   ├── models/
│   │   └── trained_model/
│   │       └── weights/
│   │           └── best.pt        # ← Trained model!
│   ├── inference/
│   │   ├── output_annotated.mp4   # ← Output video with detections
│   │   └── detections.json        # Detailed detections per frame
│   └── job_info.json              # Job metadata
```

---

## 🎬 Using the Trained Model

### Option 1: Direct Inference

```python
from ultralytics import YOLO

# Load trained model
model = YOLO("auto_train_output/abc12345/models/trained_model/weights/best.pt")

# Run on image
results = model("image.jpg")

# Run on video
results = model("video.mp4")

# Get detections
for r in results:
    for box in r.boxes:
        print(f"Class: {r.names[int(box.cls)]}, Confidence: {box.conf:.2f}")
```

### Option 2: Use in Backend

```python
# Copy trained weights to backend
cp auto_train_output/{job_id}/models/trained_model/weights/best.pt \
   app/ml/models/custom_detector.pt

# Update app/ml/yolo_infer.py to use custom model
```

---

## 🎯 Example Usage Scenarios

### Scenario 1: Detect People & Motorcycles

```bash
python auto_train.py \
  --video traffic_video.mp4 \
  --classes "person,motorcycle" \
  --epochs 20
```

### Scenario 2: Detect Weapons in Surveillance

```bash
python auto_train.py \
  --video surveillance.mp4 \
  --classes "person,weapon,knife,gun" \
  --epochs 25
```

### Scenario 3: Detect Safety Violations

```bash
python auto_train.py \
  --video construction_site.mp4 \
  --classes "helmet,person,vehicle" \
  --epochs 20
```

### Scenario 4: Via API with Progress Tracking

```python
import requests
import time

# Submit job
r = requests.post("http://localhost:8000/api/v1/models/auto-train", json={
    "video_path": "test.mp4",
    "classes": ["person", "bike", "car"],
    "epochs": 15
})
job_id = r.json()["job_id"]

# Monitor progress
while True:
    status = requests.get(
        f"http://localhost:8000/api/v1/models/auto-train/status/{job_id}"
    ).json()
    
    print(f"{status['progress']}% - {status['message']}")
    
    if status["status"] == "completed":
        print("Done! Results:", status["results"])
        break
    
    time.sleep(10)
```

---

## ⚙️ Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `video_path` | Required | Path to input video file |
| `classes` | person, motorcycle, weapon, helmet | Objects to detect |
| `epochs` | 15 | Training epochs (higher = better but slower) |
| `frame_interval` | 4 | Extract every n-th frame (4 = skip 3 frames) |
| `batch_size` | 8 | Batch size for training |
| `imgsz` | 640 | Image size for YOLO |
| `conf` | 0.4 | Confidence threshold for inference |

---

## 🚀 Performance Tips

| Setting | Speed | Accuracy | Use When |
|---------|-------|----------|----------|
| epochs=10, frame_interval=8 | ⚡ Fast | Low | Testing |
| epochs=15, frame_interval=4 | ⚡⚡ Medium | Medium | Good balance |
| epochs=25, frame_interval=2 | 🐢 Slow | ⭐⭐ High | Production |

---

## 🐛 Troubleshooting

### Issue: "YOLO-World model not found"
```bash
# Download once (one-time)
python -c "from ultralytics import YOLO; YOLO('yolov8s-world.pt')"
```

### Issue: "No frames extracted"
- Video format unsupported? Try MP4 or AVI
- Video too short? Need at least 30 frames
- Check video codec with: `ffprobe video.mp4`

### Issue: Training is very slow
- Reduce epochs: `--epochs 10`
- Increase frame_interval: `--frame-interval 8`
- Use GPU: Ensure CUDA installed

### Issue: API returns 400 "Video not found"
- Provide absolute path or place video in backend folder
- Check file permissions

---

## 📊 Expected Results

| Metric | Value |
|--------|-------|
| Frames extracted from 60s video | 75-300 (depends on frame_interval) |
| Training time per epoch | 2-5 seconds |
| Total pipeline time | 5-15 minutes (15 epochs) |
| Model size (best.pt) | ~6-11 MB |
| Output video size | 50-500 MB (depends on input) |

---

## 🔗 Integration with React Frontend

```javascript
// Upload video and start training
async function startTraining(videoFile) {
  const response = await fetch("http://localhost:8000/api/v1/models/auto-train", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      video_path: videoFile.name,
      classes: ["person", "motorcycle"],
      epochs: 15
    })
  });
  
  const data = await response.json();
  return data.job_id;
}

// Poll progress
async function checkProgress(jobId) {
  const response = await fetch(
    `http://localhost:8000/api/v1/models/auto-train/status/${jobId}`
  );
  return await response.json();
}

// Download results
async function downloadResults(jobId) {
  const response = await fetch(
    `http://localhost:8000/api/v1/models/auto-train/download/${jobId}`
  );
  return await response.json();
}
```

---

## 📚 What's Happening Behind the Scenes

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUT VIDEO FILE                          │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────▼──────────────┐
        │ YOLO-World (yolov8s-world)│  ← Zero-shot detection
        │   Auto-labels frames      │     No manual labeling!
        └────────────┬──────────────┘
                     │
        ┌────────────▼──────────────┐
        │  Generate YOLO Dataset    │
        │  - .txt annotation files  │
        │  - data.yaml config       │
        └────────────┬──────────────┘
                     │
        ┌────────────▼──────────────┐
        │ Fine-tune YOLOv8n         │  ← Training
        │ (yolov8n.pt) on custom    │
        │ dataset (15 epochs)       │
        └────────────┬──────────────┘
                     │
        ┌────────────▼──────────────┐
        │ Run Inference on Video    │  ← Detection
        │ Generate annotated output │
        └────────────┬──────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   TRAINED MODEL + OUTPUT                     │
│  ✓ best.pt (weights)                                        │
│  ✓ output_annotated.mp4 (video with boxes)                  │
│  ✓ detections.json (frame-by-frame detections)              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📞 Need Help?

Check logs:
```bash
# View API logs
# Terminal running `python run_backend.py` shows live logs

# View pipeline logs
# Check console output from `python auto_train.py`

# Check job info
cat auto_train_output/{job_id}/job_info.json
```

---

**🎉 Ready to train custom models without any manual labeling!**

Start with: `python auto_train.py --video sample.mp4 --classes person,motorcycle --epochs 15`
