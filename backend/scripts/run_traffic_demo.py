"""Run the bundled accident video through the traffic-accident event profile."""

from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.workers.detection_worker import DetectionWorker


video = BACKEND_ROOT.parent / "sample_data" / "accident_demo.mp4"
worker = DetectionWorker(analysis_mode="traffic", accident_threshold=0.52)
result = worker.process_video_stream(
    video_source=str(video),
    cam_id="traffic-validation-demo",
    conf_threshold=0.35,
    sample_every_n_frames=30,
)
print(result)
