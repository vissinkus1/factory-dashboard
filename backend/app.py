"""
Factory Productivity Dashboard - Backend API
Production-grade Flask REST API with comprehensive documentation
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_restx import Api, Resource, fields, Namespace
import os
import sys
import logging
from datetime import datetime
from functools import wraps

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from database import (
    init_db, seed_database, get_workers, get_workstations,
    insert_event, get_worker_metrics, get_workstation_metrics,
    get_factory_metrics, get_all_worker_metrics, get_all_workstation_metrics
)

# ============================================================================
# SETUP & CONFIGURATION
# ============================================================================

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend'))
CORS(app)

# Serve frontend
@app.route('/')
def serve_frontend():
    """Serve the frontend dashboard"""
    try:
        frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')
        if os.path.exists(frontend_path):
            return send_file(frontend_path)
        else:
            return {"error": "Frontend not found"}, 404
    except Exception as e:
        logger.error(f"Error serving frontend: {str(e)}")
        return {"error": str(e)}, 500

# API Setup with Swagger documentation
api = Api(
    app,
    version='1.0.0',
    title='Factory Productivity Dashboard API',
    description='Production-grade API for managing factory productivity metrics and events',
    prefix='/api',
    doc='/api/docs'
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# NAMESPACES & MODELS
# ============================================================================

# Define API namespaces
health_ns = api.namespace('health', description='Health check endpoints')
events_ns = api.namespace('events', description='Event ingestion endpoints')
workers_ns = api.namespace('workers', description='Worker data endpoints')
stations_ns = api.namespace('workstations', description='Workstation data endpoints')
metrics_ns = api.namespace('metrics', description='Metrics calculation endpoints')

# Request/Response Models
event_model = api.model('Event', {
    'timestamp': fields.String(required=True, description='ISO format timestamp'),
    'worker_id': fields.String(required=True, description='Worker identifier'),
    'workstation_id': fields.String(required=True, description='Workstation identifier'),
    'event_type': fields.String(required=True, description='Type of event (active, idle, etc)'),
    'duration_seconds': fields.Integer(description='Duration in seconds'),
    'units_produced': fields.Integer(description='Units produced'),
})

error_model = api.model('Error', {
    'error': fields.String(description='Error message'),
    'status': fields.Integer(description='HTTP status code'),
    'timestamp': fields.String(description='When error occurred'),
})

health_model = api.model('Health', {
    'status': fields.String(description='Health status'),
    'timestamp': fields.String(description='Check timestamp'),
    'version': fields.String(description='API version'),
})

# ============================================================================
# DECORATORS & UTILITIES
# ============================================================================

def validate_json(*required_fields):
    """Decorator to validate required JSON fields"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return {
                    'error': 'Request must be JSON',
                    'status': 400,
                    'timestamp': datetime.utcnow().isoformat()
                }, 400
            
            data = request.get_json()
            missing = [field for field in required_fields if field not in data]
            
            if missing:
                return {
                    'error': f'Missing required fields: {", ".join(missing)}',
                    'status': 400,
                    'timestamp': datetime.utcnow().isoformat()
                }, 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============================================================================
# INITIALIZATION
# ============================================================================

def init_database():
    """Initialize database on startup"""
    try:
        logger.info("Initializing database...")
        
        # Always ensure schema is created (CREATE TABLE IF NOT EXISTS)
        init_db()
        
        # Check if we have data
        from database import get_workers
        workers = get_workers()
        
        if not workers or len(workers) == 0:
            logger.info("Database empty, seeding with data...")
            seed_database()
            logger.info("Database seeded successfully")
        else:
            logger.info(f"Database ready with {len(workers)} workers")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

# Initialize database when app starts
init_database()

@app.before_request
def before_request():
    """Pre-request setup"""
    pass

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    logger.warning(f"404 Error: {request.path}")
    return {
        'error': 'Endpoint not found',
        'status': 404,
        'timestamp': datetime.utcnow().isoformat(),
        'path': request.path
    }, 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    logger.error(f"500 Error: {str(error)}")
    return {
        'error': 'Internal server error',
        'status': 500,
        'timestamp': datetime.utcnow().isoformat()
    }, 500

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@health_ns.route('/')
class HealthCheck(Resource):
    @health_ns.doc('get_health')
    def get(self):
        """Check API health status"""
        logger.info("Health check requested")
        return {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        }, 200

@health_ns.route('/ready')
class ReadinessCheck(Resource):
    @health_ns.doc('get_readiness')
    def get(self):
        """Check if API is ready to receive requests"""
        try:
            # Try to query workers to ensure DB is working
            get_workers()
            logger.info("Readiness check: Ready")
            return {
                'ready': True,
                'timestamp': datetime.utcnow().isoformat()
            }, 200
        except Exception as e:
            logger.error(f"Readiness check failed: {str(e)}")
            return {
                'ready': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }, 500

# ============================================================================
# WORKER ENDPOINTS
# ============================================================================

@workers_ns.route('/')
class WorkerList(Resource):
    @workers_ns.doc('list_workers')
    def get(self):
        """Get all workers with their basic information"""
        try:
            logger.info("Fetching all workers")
            workers = get_workers()
            return {
                'status': 'success',
                'count': len(workers),
                'data': workers
            }, 200
        except Exception as e:
            logger.error(f"Error fetching workers: {str(e)}")
            return {
                'error': str(e),
                'status': 500,
                'timestamp': datetime.utcnow().isoformat()
            }, 500

# ============================================================================
# WORKSTATION ENDPOINTS
# ============================================================================

@stations_ns.route('/')
class WorkstationList(Resource):
    @stations_ns.doc('list_workstations')
    def get(self):
        """Get all workstations with their basic information"""
        try:
            logger.info("Fetching all workstations")
            stations = get_workstations()
            return {
                'status': 'success',
                'count': len(stations),
                'data': stations
            }, 200
        except Exception as e:
            logger.error(f"Error fetching workstations: {str(e)}")
            return {
                'error': str(e),
                'status': 500,
                'timestamp': datetime.utcnow().isoformat()
            }, 500

# ============================================================================
# EVENT INGESTION ENDPOINTS
# ============================================================================

@events_ns.route('/')
class EventIngestion(Resource):
    @events_ns.doc('ingest_event')
    @events_ns.expect(event_model)
    def post(self):
        """Ingest a single AI event from CCTV system"""
        try:
            event_data = request.get_json()
            
            # Validate required fields
            required_fields = ['timestamp', 'worker_id', 'workstation_id', 'event_type']
            missing = [f for f in required_fields if f not in event_data]
            
            if missing:
                logger.warning(f"Missing fields in event: {missing}")
                return {
                    'error': f'Missing required fields: {", ".join(missing)}',
                    'status': 400,
                    'timestamp': datetime.utcnow().isoformat()
                }, 400
            
            if insert_event(event_data):
                logger.info(f"Event ingested: {event_data['worker_id']}")
                return {
                    'message': 'Event ingested successfully',
                    'status': 201,
                    'timestamp': datetime.utcnow().isoformat()
                }, 201
            else:
                logger.error("Failed to insert event")
                return {
                    'error': 'Failed to insert event',
                    'status': 500,
                    'timestamp': datetime.utcnow().isoformat()
                }, 500
        except Exception as e:
            logger.error(f"Error ingesting event: {str(e)}")
            return {
                'error': str(e),
                'status': 500,
                'timestamp': datetime.utcnow().isoformat()
            }, 500

@events_ns.route('/batch')
class EventBatchIngestion(Resource):
    @events_ns.doc('ingest_events_batch')
    def post(self):
        """Ingest multiple AI events in batch (bulk import)"""
        try:
            events = request.get_json()
            
            if not isinstance(events, list):
                logger.warning("Batch request is not a list")
                return {
                    'error': 'Expected a list of events',
                    'status': 400,
                    'timestamp': datetime.utcnow().isoformat()
                }, 400
            
            success_count = 0
            failed_events = []
            
            for idx, event_data in enumerate(events):
                try:
                    if insert_event(event_data):
                        success_count += 1
                    else:
                        failed_events.append(idx)
                except Exception as e:
                    logger.warning(f"Failed to insert event {idx}: {str(e)}")
                    failed_events.append(idx)
            
            logger.info(f"Batch ingestion completed: {success_count}/{len(events)} successful")
            
            return {
                'message': f'{success_count}/{len(events)} events ingested successfully',
                'success_count': success_count,
                'failed_count': len(failed_events),
                'total_count': len(events),
                'failed_indices': failed_events,
                'timestamp': datetime.utcnow().isoformat()
            }, 201
        except Exception as e:
            logger.error(f"Error in batch ingestion: {str(e)}")
            return {
                'error': str(e),
                'status': 500,
                'timestamp': datetime.utcnow().isoformat()
            }, 500

# ============================================================================
# METRICS ENDPOINTS
# ============================================================================

@metrics_ns.route('/factory')
class FactoryMetrics(Resource):
    @metrics_ns.doc('factory_metrics')
    def get(self):
        """Get factory-level aggregated productivity metrics"""
        try:
            logger.info("Fetching factory metrics")
            metrics = get_factory_metrics()
            return {
                'status': 'success',
                'data': metrics,
                'timestamp': datetime.utcnow().isoformat()
            }, 200
        except Exception as e:
            logger.error(f"Error fetching factory metrics: {str(e)}")
            return {
                'error': str(e),
                'status': 500,
                'timestamp': datetime.utcnow().isoformat()
            }, 500

@metrics_ns.route('/workers')
class WorkersMetrics(Resource):
    @metrics_ns.doc('all_workers_metrics')
    def get(self):
        """Get productivity metrics for all workers"""
        try:
            logger.info("Fetching metrics for all workers")
            metrics = get_all_worker_metrics()
            return {
                'status': 'success',
                'count': len(metrics),
                'data': metrics,
                'timestamp': datetime.utcnow().isoformat()
            }, 200
        except Exception as e:
            logger.error(f"Error fetching workers metrics: {str(e)}")
            return {
                'error': str(e),
                'status': 500,
                'timestamp': datetime.utcnow().isoformat()
            }, 500

@metrics_ns.route('/workers/<worker_id>')
class WorkerMetricsDetail(Resource):
    @metrics_ns.doc('worker_metrics_detail', params={'worker_id': 'The worker identifier'})
    def get(self, worker_id):
        """Get detailed productivity metrics for a specific worker"""
        try:
            logger.info(f"Fetching metrics for worker: {worker_id}")
            metrics = get_worker_metrics(worker_id)
            
            if not metrics:
                logger.warning(f"Worker not found: {worker_id}")
                return {
                    'error': 'Worker not found',
                    'status': 404,
                    'worker_id': worker_id,
                    'timestamp': datetime.utcnow().isoformat()
                }, 404
            
            return {
                'status': 'success',
                'data': metrics,
                'timestamp': datetime.utcnow().isoformat()
            }, 200
        except Exception as e:
            logger.error(f"Error fetching worker {worker_id} metrics: {str(e)}")
            return {
                'error': str(e),
                'status': 500,
                'timestamp': datetime.utcnow().isoformat()
            }, 500

@metrics_ns.route('/workstations')
class WorkstationsMetrics(Resource):
    @metrics_ns.doc('all_workstations_metrics')
    def get(self):
        """Get productivity metrics for all workstations"""
        try:
            logger.info("Fetching metrics for all workstations")
            metrics = get_all_workstation_metrics()
            return {
                'status': 'success',
                'count': len(metrics),
                'data': metrics,
                'timestamp': datetime.utcnow().isoformat()
            }, 200
        except Exception as e:
            logger.error(f"Error fetching workstations metrics: {str(e)}")
            return {
                'error': str(e),
                'status': 500,
                'timestamp': datetime.utcnow().isoformat()
            }, 500

@metrics_ns.route('/workstations/<station_id>')
class WorkstationMetricsDetail(Resource):
    @metrics_ns.doc('workstation_metrics_detail', params={'station_id': 'The workstation identifier'})
    def get(self, station_id):
        """Get detailed productivity metrics for a specific workstation"""
        try:
            logger.info(f"Fetching metrics for workstation: {station_id}")
            metrics = get_workstation_metrics(station_id)
            
            if not metrics:
                logger.warning(f"Workstation not found: {station_id}")
                return {
                    'error': 'Workstation not found',
                    'status': 404,
                    'station_id': station_id,
                    'timestamp': datetime.utcnow().isoformat()
                }, 404
            
            return {
                'status': 'success',
                'data': metrics,
                'timestamp': datetime.utcnow().isoformat()
            }, 200
        except Exception as e:
            logger.error(f"Error fetching workstation {station_id} metrics: {str(e)}")
            return {
                'error': str(e),
                'status': 500,
                'timestamp': datetime.utcnow().isoformat()
            }, 500

# ============================================================================
# MAINTENANCE ENDPOINTS
# ============================================================================

@health_ns.route('/seed')
class DatabaseSeed(Resource):
    @health_ns.doc('seed_database')
    def post(self):
        """Reset and seed database with dummy data (Admin only - for testing)"""
        try:
            logger.warning("Database seed requested - this will clear all data")
            seed_database()
            logger.info("Database seeded successfully")
            return {
                'message': 'Database seeded successfully',
                'status': 200,
                'timestamp': datetime.utcnow().isoformat()
            }, 200
        except Exception as e:
            logger.error(f"Error seeding database: {str(e)}")
            return {
                'error': str(e),
                'status': 500,
                'timestamp': datetime.utcnow().isoformat()
            }, 500

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    logger.info("Starting Factory Productivity Dashboard API")
    logger.info("Documentation available at: http://localhost:5000/docs")
    app.run(host='0.0.0.0', port=5000, debug=False)

