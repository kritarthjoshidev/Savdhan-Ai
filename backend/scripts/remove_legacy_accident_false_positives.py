"""Remove the old border-rule false positives created from the accident demo.

This intentionally targets only the known generated records from the earlier
pipeline: ``accident-demo-cam`` / ``border-5`` / ``INTRUSION``. It never
touches manually reviewed incidents or the new traffic-classified results.
"""

from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.database import SessionLocal
from app.db.models import Incident, Snapshot
from app.services.storage import get_storage


CAMERA_ID = "accident-demo-cam"
TRACK_ID = "border-5"


def main() -> None:
    db = SessionLocal()
    try:
        candidates = (
            db.query(Incident)
            .filter(Incident.source_cam == CAMERA_ID, Incident.track_id == TRACK_ID)
            .all()
        )
        false_positives = [
            item
            for item in candidates
            if (item.meta or {}).get("event_type") == "INTRUSION"
        ]
        storage = get_storage()
        for incident in false_positives:
            if incident.snapshot_path:
                storage.delete_object(incident.snapshot_path)
            db.query(Snapshot).filter(Snapshot.incident_id == incident.id).delete()
            db.delete(incident)
        db.commit()
        print(f"Removed {len(false_positives)} old accident-demo false positives.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
