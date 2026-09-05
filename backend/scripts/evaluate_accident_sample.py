"""Quick local check for the bundled accident demo's CLIP scene classifier."""

from pathlib import Path
import sys

import cv2

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.ml.scene_events import SceneEventClassifier


video = Path(__file__).resolve().parents[2] / "sample_data" / "accident_demo.mp4"
classifier = SceneEventClassifier()
capture = cv2.VideoCapture(str(video))

try:
    for frame_id in (600, 630, 660, 675, 690, 720):
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ok, frame = capture.read()
        if not ok:
            raise RuntimeError(f"Could not read frame {frame_id}")
        result = classifier.classify(frame)
        print(frame_id, result["domain"], result["scores"])
finally:
    capture.release()
