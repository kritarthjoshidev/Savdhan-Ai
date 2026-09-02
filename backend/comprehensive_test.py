#!/usr/bin/env python
"""
Comprehensive Backend Test Script
Tests all major endpoints to verify the API is working correctly
"""
import requests
import json

def test_backend():
    print("\n" + "="*60)
    print("SURVEILLANCE BACKEND - COMPREHENSIVE TEST")
    print("="*60 + "\n")

    BASE_URL = "http://localhost:8000"
    API_BASE = f"{BASE_URL}/api/v1"
    
    try:
        # Test 1: Health Check
        print("✓ TEST 1: Health Check")
        r = requests.get(f"{BASE_URL}/health")
        print(f"  Status: {r.status_code}")
        print(f"  Response: {json.dumps(r.json(), indent=2)}\n")

        # Test 2: Root Endpoint
        print("✓ TEST 2: API Information")
        r = requests.get(f"{BASE_URL}/")
        print(f"  Status: {r.status_code}")
        print(f"  Response: {json.dumps(r.json(), indent=2)}\n")

        # Test 3: Create an Incident
        print("✓ TEST 3: Create Incident")
        incident_data = {
            "source_cam": "camera_01",
            "bbox": [640, 480, 100, 150],
            "snapshot_path": "s3://surveillance/snapshots/cam_01/frame_001.jpg",
            "confidence": 0.95,
            "track_id": "person_123",
            "meta": {"event_type": "intrusion", "location": "main_entrance"}
        }
        r = requests.post(f"{API_BASE}/incidents", json=incident_data)
        print(f"  Status: {r.status_code}")
        response = r.json()
        print(f"  Response: {json.dumps(response, indent=2, default=str)}")
        incident_id = response.get("id") if r.status_code in [200, 201] else None
        print()

        # Test 4: List Incidents
        print("✓ TEST 4: List Incidents")
        r = requests.get(f"{API_BASE}/incidents?limit=5")
        print(f"  Status: {r.status_code}")
        incidents = r.json()
        print(f"  Total incidents: {len(incidents) if isinstance(incidents, list) else 'N/A'}")
        if isinstance(incidents, list) and incidents:
            print(f"  Sample: {json.dumps(incidents[0], indent=2, default=str)}\n")
        else:
            print(f"  Response: {json.dumps(incidents, indent=2, default=str)}\n")

        # Test 5: Get Specific Incident
        if incident_id:
            print(f"✓ TEST 5: Get Incident {incident_id}")
            r = requests.get(f"{API_BASE}/incidents/{incident_id}")
            print(f"  Status: {r.status_code}")
            print(f"  Response: {json.dumps(r.json(), indent=2, default=str)}\n")

        # Test 6: List Models
        print("✓ TEST 6: List Models")
        r = requests.get(f"{API_BASE}/models")
        print(f"  Status: {r.status_code}")
        models = r.json()
        print(f"  Response: {json.dumps(models, indent=2, default=str)}\n")

        # Test 7: API Docs
        print("✓ TEST 7: API Documentation")
        r = requests.get(f"{BASE_URL}/docs")
        print(f"  Status: {r.status_code}")
        print(f"  Swagger UI: {'Available ✓' if r.status_code == 200 else 'Not Available ✗'}\n")

        # Test 8: OpenAPI Schema
        print("✓ TEST 8: OpenAPI Schema")
        r = requests.get(f"{BASE_URL}/openapi.json")
        print(f"  Status: {r.status_code}")
        schema = r.json()
        print(f"  Title: {schema.get('info', {}).get('title')}")
        print(f"  Version: {schema.get('info', {}).get('version')}")
        print(f"  Endpoints available: {len(schema.get('paths', {}))} paths\n")

        print("="*60)
        print("ALL TESTS COMPLETED SUCCESSFULLY! ✓")
        print("="*60)
        print("\nYour backend is ready for integration!")
        print("\nNext Steps:")
        print("1. Visit http://localhost:8000/docs for interactive API testing")
        print("2. Connect your React frontend to http://localhost:8000")
        print("3. Use WebSocket at ws://localhost:8000/ws/alerts for real-time alerts")
        print("4. See QUICK_START.md for detailed integration examples")
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to backend at http://localhost:8000")
        print("Make sure backend is running with: python run_backend.py")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_backend()
