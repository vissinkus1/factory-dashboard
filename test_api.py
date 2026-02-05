#!/usr/bin/env python3
"""
Test script for Factory Productivity Dashboard

This script tests the backend API endpoints and validates the system setup.
"""

import requests
import json
import time
from datetime import datetime, timedelta

API_BASE = 'http://localhost:5000/api'

def test_health():
    """Test health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get('http://localhost:5000/health')
        assert response.status_code == 200
        print("✓ Health check passed")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_seed():
    """Test database seeding"""
    print("Testing database seed...")
    try:
        response = requests.post(f'{API_BASE}/seed')
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        print("✓ Database seed successful")
        return True
    except Exception as e:
        print(f"✗ Database seed failed: {e}")
        return False

def test_get_workers():
    """Test get workers endpoint"""
    print("Testing get workers...")
    try:
        response = requests.get(f'{API_BASE}/workers')
        assert response.status_code == 200
        workers = response.json()
        assert len(workers) == 6
        assert all('worker_id' in w and 'name' in w for w in workers)
        print(f"✓ Retrieved {len(workers)} workers")
        return True
    except Exception as e:
        print(f"✗ Get workers failed: {e}")
        return False

def test_get_workstations():
    """Test get workstations endpoint"""
    print("Testing get workstations...")
    try:
        response = requests.get(f'{API_BASE}/workstations')
        assert response.status_code == 200
        stations = response.json()
        assert len(stations) == 6
        assert all('station_id' in s and 'name' in s for s in stations)
        print(f"✓ Retrieved {len(stations)} workstations")
        return True
    except Exception as e:
        print(f"✗ Get workstations failed: {e}")
        return False

def test_ingest_event():
    """Test single event ingestion"""
    print("Testing event ingestion...")
    try:
        event = {
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "worker_id": "W1",
            "workstation_id": "S1",
            "event_type": "working",
            "confidence": 0.95,
            "count": 0
        }
        response = requests.post(f'{API_BASE}/events', json=event)
        assert response.status_code == 201
        print("✓ Event ingestion successful")
        return True
    except Exception as e:
        print(f"✗ Event ingestion failed: {e}")
        return False

def test_batch_ingest():
    """Test batch event ingestion"""
    print("Testing batch event ingestion...")
    try:
        events = []
        base_time = datetime.utcnow()
        for i in range(5):
            events.append({
                "timestamp": (base_time + timedelta(seconds=i*60)).isoformat() + 'Z',
                "worker_id": f"W{(i % 6) + 1}",
                "workstation_id": f"S{(i % 6) + 1}",
                "event_type": "working",
                "confidence": 0.92,
                "count": 0
            })
        
        response = requests.post(f'{API_BASE}/events/batch', json=events)
        assert response.status_code == 201
        data = response.json()
        assert data['success_count'] == 5
        print(f"✓ Batch ingestion successful ({data['success_count']} events)")
        return True
    except Exception as e:
        print(f"✗ Batch ingestion failed: {e}")
        return False

def test_factory_metrics():
    """Test factory metrics endpoint"""
    print("Testing factory metrics...")
    try:
        response = requests.get(f'{API_BASE}/metrics/factory')
        assert response.status_code == 200
        metrics = response.json()
        required_fields = [
            'total_productive_time_hours',
            'total_production_count',
            'average_production_rate',
            'average_utilization_percentage',
            'worker_count',
            'station_count'
        ]
        assert all(field in metrics for field in required_fields)
        print(f"✓ Factory metrics retrieved")
        print(f"  - Productive hours: {metrics['total_productive_time_hours']}")
        print(f"  - Total production: {metrics['total_production_count']} units")
        print(f"  - Avg utilization: {metrics['average_utilization_percentage']}%")
        return True
    except Exception as e:
        print(f"✗ Factory metrics failed: {e}")
        return False

def test_worker_metrics():
    """Test worker metrics endpoint"""
    print("Testing worker metrics...")
    try:
        response = requests.get(f'{API_BASE}/metrics/workers')
        assert response.status_code == 200
        workers = response.json()
        assert len(workers) == 6
        required_fields = [
            'worker_id',
            'name',
            'total_active_time_hours',
            'total_idle_time_hours',
            'utilization_percentage',
            'total_units_produced',
            'units_per_hour'
        ]
        assert all(field in workers[0] for field in required_fields)
        print(f"✓ Worker metrics retrieved for {len(workers)} workers")
        for w in workers[:2]:
            print(f"  - {w['name']}: {w['utilization_percentage']}% utilization")
        return True
    except Exception as e:
        print(f"✗ Worker metrics failed: {e}")
        return False

def test_workstation_metrics():
    """Test workstation metrics endpoint"""
    print("Testing workstation metrics...")
    try:
        response = requests.get(f'{API_BASE}/metrics/workstations')
        assert response.status_code == 200
        stations = response.json()
        assert len(stations) == 6
        required_fields = [
            'station_id',
            'name',
            'occupancy_time_hours',
            'utilization_percentage',
            'total_units_produced',
            'throughput_rate'
        ]
        assert all(field in stations[0] for field in required_fields)
        print(f"✓ Workstation metrics retrieved for {len(stations)} stations")
        for s in stations[:2]:
            print(f"  - {s['name']}: {s['throughput_rate']} units/hour")
        return True
    except Exception as e:
        print(f"✗ Workstation metrics failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Factory Productivity Dashboard - API Tests")
    print("=" * 60)
    print()
    
    # Check if server is running
    try:
        requests.get('http://localhost:5000/health')
    except:
        print("ERROR: Backend server not running!")
        print("Please start the backend with: python backend/app.py")
        print()
        return False
    
    tests = [
        test_health,
        test_seed,
        test_get_workers,
        test_get_workstations,
        test_ingest_event,
        test_batch_ingest,
        test_factory_metrics,
        test_worker_metrics,
        test_workstation_metrics,
    ]
    
    results = []
    for test in tests:
        results.append(test())
        print()
        time.sleep(0.5)
    
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("✓ All tests passed! System is ready to use.")
        print()
        print("Dashboard URLs:")
        print("  - Frontend: http://localhost:8080")
        print("  - Backend API: http://localhost:5000")
        return True
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
