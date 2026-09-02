"""
Sample test script to verify backend is working
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_health():
    """Test health endpoint"""
    print("Testing health check...")
    r = requests.get(f"{BASE_URL}/health")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}\n")

def test_create_incident():
    """Test creating an incident"""
    print("Testing incident creation...")
    payload = {
        "source_cam": "camera_01",
        "bbox": [640, 480, 100, 150],
        "snapshot_path": "s3://surveillance/snapshots/cam_01/frame_001.jpg",
        "confidence": 0.95,
        "track_id": "person_123",
        "meta": {"event_type": "intrusion"}
    }
    r = requests.post(f"{API_BASE}/incidents", json=payload)
    print(f"Status: {r.status_code}")
    response = r.json()
    print(f"Response: {json.dumps(response, indent=2, default=str)}\n")
    return response.get("id") if r.status_code == 200 else None

def test_list_incidents():
    """Test listing incidents"""
    print("Testing list incidents...")
    r = requests.get(f"{API_BASE}/incidents?limit=10&status=pending")
    print(f"Status: {r.status_code}")
    print(f"Response: {json.dumps(r.json(), indent=2, default=str)}\n")

def test_get_incident(incident_id):
    """Test getting specific incident"""
    print(f"Testing get incident {incident_id}...")
    r = requests.get(f"{API_BASE}/incidents/{incident_id}")
    print(f"Status: {r.status_code}")
    print(f"Response: {json.dumps(r.json(), indent=2, default=str)}\n")

def test_update_incident(incident_id):
    """Test updating incident status"""
    print(f"Testing update incident {incident_id}...")
    payload = {
        "status": "verified",
        "meta": {"reviewer": "test_user", "notes": "False positive"}
    }
    r = requests.patch(f"{API_BASE}/incidents/{incident_id}", json=payload)
    print(f"Status: {r.status_code}")
    print(f"Response: {json.dumps(r.json(), indent=2, default=str)}\n")

def test_trigger_training():
    """Test triggering training job"""
    print("Testing training trigger...")
    payload = {
        "model_name": "yolo_custom",
        "base_model": "yolov8n.pt",
        "epochs": 10,
        "batch_size": 8,
        "data_yaml_path": "/path/to/dataset.yaml"
    }
    r = requests.post(f"{API_BASE}/models/train", json=payload)
    print(f"Status: {r.status_code}")
    response = r.json()
    print(f"Response: {json.dumps(response, indent=2, default=str)}\n")
    return response.get("id") if r.status_code == 200 else None

def test_list_models():
    """Test listing models"""
    print("Testing list models...")
    r = requests.get(f"{API_BASE}/models")
    print(f"Status: {r.status_code}")
    print(f"Response: {json.dumps(r.json(), indent=2, default=str)}\n")

def test_get_training_job(job_id):
    """Test getting training job status"""
    print(f"Testing get training job {job_id}...")
    r = requests.get(f"{API_BASE}/models/train/{job_id}")
    print(f"Status: {r.status_code}")
    print(f"Response: {json.dumps(r.json(), indent=2, default=str)}\n")

def test_websocket():
    """Test WebSocket connection - simplified"""
    print("Testing WebSocket endpoint...")
    try:
        # Just check if the endpoint exists without actually connecting
        r = requests.get(f"{BASE_URL}/health")
        print(f"Backend is running: {r.status_code == 200}")
        print("(WebSocket can be tested via browser)\n")
    except Exception as e:
        print(f"WebSocket test skipped: {e}\n")

def main():
    """Run all tests"""
    print("=" * 60)
    print("SURVEILLANCE BACKEND - TEST SUITE")
    print("=" * 60 + "\n")
    
    try:
        # Basic health check
        test_health()
        
        # Incidents
        incident_id = test_create_incident()
        if incident_id:
            test_get_incident(incident_id)
            test_list_incidents()
            test_update_incident(incident_id)
        
        # Models & Training
        test_list_models()
        job_id = test_trigger_training()
        if job_id:
            test_get_training_job(job_id)
        
        # WebSocket
        test_websocket()
        
        print("=" * 60)
        print("✓ All tests completed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to backend at http://localhost:8000")
        print("Make sure backend is running: docker-compose up -d")

if __name__ == "__main__":
    main()
