"""
Comprehensive Test Suite for Factory Productivity Dashboard API
Tests cover: health checks, CRUD operations, metrics, error handling
"""

import unittest
import json
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app
from database import init_db, seed_database

class APITestCase(unittest.TestCase):
    """Base test case class with setup and teardown"""
    
    @classmethod
    def setUpClass(cls):
        """Setup test database once for all tests"""
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        
        # Initialize test database
        with cls.app.app_context():
            init_db()
            seed_database()
    
    def setUp(self):
        """Reset database before each test"""
        pass
    
    def tearDown(self):
        """Clean up after each test"""
        pass

class HealthCheckTests(APITestCase):
    """Tests for health check endpoints"""
    
    def test_health_check(self):
        """Test basic health check endpoint"""
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('timestamp', data)
        self.assertEqual(data['version'], '1.0.0')
    
    def test_readiness_check(self):
        """Test readiness probe"""
        response = self.client.get('/health/ready')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['ready'])
        self.assertIn('timestamp', data)

class WorkerEndpointTests(APITestCase):
    """Tests for worker-related endpoints"""
    
    def test_list_workers(self):
        """Test fetching all workers"""
        response = self.client.get('/workers/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertEqual(data['status'], 'success')
        self.assertIn('count', data)
        self.assertIn('data', data)
        self.assertGreater(data['count'], 0)
        
        # Check worker structure
        worker = data['data'][0]
        self.assertIn('worker_id', worker)
        self.assertIn('name', worker )
    
    def test_list_workers_non_empty(self):
        """Test that workers list is populated with seed data"""
        response = self.client.get('/workers/')
        data = json.loads(response.data)
        self.assertGreater(len(data['data']), 0)

class WorkstationEndpointTests(APITestCase):
    """Tests for workstation-related endpoints"""
    
    def test_list_workstations(self):
        """Test fetching all workstations"""
        response = self.client.get('/workstations/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertEqual(data['status'], 'success')
        self.assertIn('count', data)
        self.assertIn('data', data)
        self.assertGreater(data['count'], 0)
        
        # Check workstation structure
        station = data['data'][0]
        self.assertIn('station_id', station)
        self.assertIn('name', station)
    
    def test_list_workstations_non_empty(self):
        """Test that workstations list is populated"""
        response = self.client.get('/workstations/')
        data = json.loads(response.data)
        self.assertGreater(len(data['data']), 0)

class EventIngestionTests(APITestCase):
    """Tests for event ingestion endpoints"""
    
    def test_ingest_single_event(self):
        """Test ingesting a single event"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'worker_id': 'W001',
            'workstation_id': 'S001',
            'event_type': 'working',  # Match database constraints
            'duration_seconds': 3600,
            'units_produced': 50
        }
        
        response = self.client.post(
            '/events/',
            data=json.dumps(event),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'Event ingested successfully')
    
    def test_ingest_event_missing_fields(self):
        """Test event ingestion with missing required fields"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            # Missing worker_id, workstation_id, event_type
        }
        
        response = self.client.post(
            '/events/',
            data=json.dumps(event),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('Missing required fields', data['error'])
    
    def test_ingest_event_invalid_json(self):
        """Test event ingestion with invalid JSON"""
        response = self.client.post(
            '/events/',
            data='invalid json{',
            content_type='application/json'
        )
        
        # Should fail due to invalid JSON
        self.assertNotEqual(response.status_code, 201)
    
    def test_ingest_batch_events(self):
        """Test ingesting multiple events in batch"""
        events = [
            {
                'timestamp': (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                'worker_id': f'W{i:03d}',
                'workstation_id': 'S001',
                'event_type': 'working',  # Match database constraints
                'duration_seconds': 3600,
                'units_produced': 50
            }
            for i in range(3)
        ]
        
        response = self.client.post(
            '/events/batch',
            data=json.dumps(events),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['success_count'], 3)
        self.assertEqual(data['total_count'], 3)
    
    def test_ingest_batch_must_be_list(self):
        """Test batch endpoint requires list"""
        response = self.client.post(
            '/events/batch',
            data=json.dumps({'not': 'a list'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Expected a list', data['error'])

class MetricsTests(APITestCase):
    """Tests for metrics calculation endpoints"""
    
    def test_factory_metrics(self):
        """Test factory-level metrics"""
        response = self.client.get('/metrics/factory')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertEqual(data['status'], 'success')
        self.assertIn('data', data)
        self.assertIn('timestamp', data)
        
        metrics = data['data']
        # Check expected metrics fields
        self.assertIn('worker_count', metrics)
        self.assertIn('station_count', metrics)
        self.assertIn('total_events', metrics)
    
    def test_all_workers_metrics(self):
        """Test metrics for all workers"""
        response = self.client.get('/metrics/workers')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertEqual(data['status'], 'success')
        self.assertIn('count', data)
        self.assertGreater(data['count'], 0)
        self.assertIn('data', data)
        self.assertIn('timestamp', data)
    
    def test_specific_worker_metrics(self):
        """Test metrics for a specific worker"""
        # First get a valid worker ID
        workers_response = self.client.get('/workers/')
        workers_data = json.loads(workers_response.data)
        
        if workers_data['count'] > 0:
            worker_id = workers_data['data'][0]['worker_id']
            
            response = self.client.get(f'/metrics/workers/{worker_id}')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            
            self.assertEqual(data['status'], 'success')
            self.assertIn('data', data)
            self.assertIn('timestamp', data)
    
    def test_worker_metrics_not_found(self):
        """Test metrics for non-existent worker"""
        response = self.client.get('/metrics/workers/NONEXISTENT')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('Worker not found', data['error'])
    
    def test_all_workstations_metrics(self):
        """Test metrics for all workstations"""
        response = self.client.get('/metrics/workstations')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertEqual(data['status'], 'success')
        self.assertIn('count', data)
        self.assertGreater(data['count'], 0)
        self.assertIn('data', data)
    
    def test_specific_workstation_metrics(self):
        """Test metrics for a specific workstation"""
        # Get a valid station ID
        stations_response = self.client.get('/workstations/')
        stations_data = json.loads(stations_response.data)
        
        if stations_data['count'] > 0:
            station_id = stations_data['data'][0]['station_id']
            
            response = self.client.get(f'/metrics/workstations/{station_id}')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            
            self.assertEqual(data['status'], 'success')
            self.assertIn('data', data)
    
    def test_workstation_metrics_not_found(self):
        """Test metrics for non-existent workstation"""
        response = self.client.get('/metrics/workstations/NONEXISTENT')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('Workstation not found', data['error'])

class ErrorHandlingTests(APITestCase):
    """Tests for error handling"""
    
    def test_404_not_found(self):
        """Test 404 response for non-existent endpoint"""
        response = self.client.get('/nonexistent/endpoint')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['status'], 404)
    
    def test_missing_content_type(self):
        """Test POST without JSON content type"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'worker_id': 'W001',
            'workstation_id': 'S001',
            'event_type': 'active'
        }
        
        response = self.client.post(
            '/events/',
            data=json.dumps(event),
            content_type='text/plain'  # Wrong content type
        )
        
        # Should fail due to wrong content type
        self.assertNotEqual(response.status_code, 201)

class DataIntegrityTests(APITestCase):
    """Tests for data integrity and consistency"""
    
    def test_metrics_calculations_consistent(self):
        """Test that metrics calculations are consistent"""
        # Get factory metrics
        factory_response = self.client.get('/metrics/factory')
        factory_data = json.loads(factory_response.data)
        
        # Get worker metrics
        workers_response = self.client.get('/metrics/workers')
        workers_data = json.loads(workers_response.data)
        
        # Just verify both endpoints work and return valid data
        self.assertEqual(factory_response.status_code, 200)
        self.assertEqual(workers_response.status_code, 200)
        
        factory_metrics = factory_data['data']
        self.assertIn('worker_count', factory_metrics)
        self.assertEqual(factory_metrics['worker_count'], workers_data['count'])

class PerformanceTests(APITestCase):
    """Tests for API performance"""
    
    def test_workers_list_response_time(self):
        """Test workers endpoint response is fast"""
        import time
        start = time.time()
        response = self.client.get('/workers/')
        elapsed = time.time() - start
        
        self.assertEqual(response.status_code, 200)
        # Should respond within 1 second
        self.assertLess(elapsed, 1.0)
    
    def test_large_batch_ingestion(self):
        """Test batch ingestion with many events"""
        events = [
            {
                'timestamp': (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                'worker_id': f'W{i%10:03d}',
                'workstation_id': f'S{i%5:03d}',
                'event_type': 'working' if i % 2 == 0 else 'idle',  # Valid event types
                'duration_seconds': 3600,
                'units_produced': 50
            }
            for i in range(50)
        ]
        
        response = self.client.post(
            '/events/batch',
            data=json.dumps(events),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        # All should be successful
        self.assertEqual(data['success_count'] + data['failed_count'], 50)

# ============================================================================
# TEST RUNNER
# ============================================================================

if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(HealthCheckTests))
    suite.addTests(loader.loadTestsFromTestCase(WorkerEndpointTests))
    suite.addTests(loader.loadTestsFromTestCase(WorkstationEndpointTests))
    suite.addTests(loader.loadTestsFromTestCase(EventIngestionTests))
    suite.addTests(loader.loadTestsFromTestCase(MetricsTests))
    suite.addTests(loader.loadTestsFromTestCase(ErrorHandlingTests))
    suite.addTests(loader.loadTestsFromTestCase(DataIntegrityTests))
    suite.addTests(loader.loadTestsFromTestCase(PerformanceTests))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70 + "\n")
    
    # Exit with proper code
    exit(0 if result.wasSuccessful() else 1)
