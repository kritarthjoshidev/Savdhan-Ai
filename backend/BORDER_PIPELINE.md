# SIH border-surveillance backend pipeline

```
MP4 / RTSP camera
  -> motion gate (MOG2 + persistence)
  -> CLAHE low-light enhancement
  -> YOLO-World (person, vehicle, weapon, backpack)
  -> per-camera virtual fence
  -> OSNet person Re-ID gallery
  -> snapshot storage + incident database row
  -> WebSocket alert: INTRUSION
```

## Cloned-repository integration decisions

| Repository | Decision | Backend implementation |
| --- | --- | --- |
| `motion-detection-alert-system` | Integrated safely | Its MOG2, contour-area, and persistence concept is implemented in `app/ml/motion_gate.py`. No Telegram code, secrets, or external credentials are used. |
| `reidentification-fr` | Integrated | Its YOLO-person-crop -> OSNet -> cosine similarity pattern is implemented in `app/ml/reid_embed.py` and `workers/detection_worker.py`. Each intrusion stores a real 512-d OSNet embedding in the `snapshots` gallery. |
| `DeepCamera` | Architecture reference, not embedded | It is an independent platform, so running its Docker/skill stack inside this FastAPI service would create a competing pipeline. We adopted the portable CPU-first, frame-governor style with `sample_every_n_frames` and a pluggable pipeline boundary. |
| `A-AI` | Not integrated by design | It is a separate Next.js frontend. Frontend work is assigned to Antigravity, so this backend neither imports nor changes it. |
| `my-projects` | Not integrated | It is a collection of unrelated notebooks; no surveillance module is suitable for this system. |

## Local demo mode

Set `STORAGE_BACKEND=local` to save snapshots under `backend/data/` without Docker.
The Docker compose stack sets `STORAGE_BACKEND=minio` so the same worker stores snapshots in MinIO.

Run a recording from the `backend` folder:

```powershell
py -3.14 scripts/run_border_demo.py "C:\path\to\video.mp4" `
  --camera-id border-demo-01 `
  --sample-every-n-frames 30
```

For a 30 FPS video, sample every 30 frames for one inference per second on CPU. A valid `INTRUSION` requires a `person` centroid to cross from above to below the horizontal virtual-fence line. A normal accident/city video can produce person or vehicle detections but correctly produce zero border-intrusion events.
