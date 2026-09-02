"""Run a local video through the SIH border-surveillance backend pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.db.database import init_db
from app.workers.detection_worker import DetectionWorker


def main() -> None:
    parser = argparse.ArgumentParser(description="Process a recording for border intrusions")
    parser.add_argument("video", type=Path, help="Path to an MP4/MOV/AVI recording")
    parser.add_argument("--camera-id", default="demo-border-cam")
    parser.add_argument("--confidence", type=float, default=0.30)
    parser.add_argument("--fence-y-ratio", type=float, default=0.50)
    parser.add_argument(
        "--sample-every-n-frames",
        type=int,
        default=30,
        help="Use 30 for CPU demos at 30 FPS (about one inference per second).",
    )
    args = parser.parse_args()

    if not args.video.is_file():
        parser.error(f"Video does not exist: {args.video}")

    init_db()
    worker = DetectionWorker(fence_y_ratio=args.fence_y_ratio)
    report = worker.process_video_stream(
        video_source=str(args.video),
        cam_id=args.camera_id,
        conf_threshold=args.confidence,
        sample_every_n_frames=args.sample_every_n_frames,
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
