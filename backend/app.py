from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys

# Add parent directory to path to import database module
sys.path.insert(0, os.path.dirname(__file__))

from database import (
    init_db, seed_database, get_workers, get_workstations,
    insert_event, get_worker_metrics, get_workstation_metrics,
    get_factory_metrics, get_all_worker_metrics, get_all_workstation_metrics
)

app = Flask(__name__)
CORS(app)

# Initialize database on startup
@app.before_request
def startup():
    """Initialize DB if needed"""
    db_path = os.path.join(os.path.dirname(__file__), 'factory_dashboard.db')
    if not os.path.exists(db_path):
        init_db()
        seed_database()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/seed', methods=['POST'])
def seed():
    """Reset and seed database with dummy data"""
    try:
        seed_database()
        return jsonify({'message': 'Database seeded successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workers', methods=['GET'])
def list_workers():
    """Get all workers"""
    try:
        workers = get_workers()
        return jsonify(workers), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workstations', methods=['GET'])
def list_workstations():
    """Get all workstations"""
    try:
        stations = get_workstations()
        return jsonify(stations), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/events', methods=['POST'])
def ingest_event():
    """Ingest a single AI event"""
    try:
        event_data = request.get_json()
        
        # Validate required fields
        required_fields = ['timestamp', 'worker_id', 'workstation_id', 'event_type']
        if not all(field in event_data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if insert_event(event_data):
            return jsonify({'message': 'Event ingested successfully'}), 201
        else:
            return jsonify({'error': 'Failed to insert event'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/events/batch', methods=['POST'])
def ingest_events_batch():
    """Ingest multiple AI events"""
    try:
        events = request.get_json()
        
        if not isinstance(events, list):
            return jsonify({'error': 'Expected a list of events'}), 400
        
        success_count = 0
        for event_data in events:
            if insert_event(event_data):
                success_count += 1
        
        return jsonify({
            'message': f'{success_count}/{len(events)} events ingested successfully',
            'success_count': success_count,
            'total_count': len(events)
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/factory', methods=['GET'])
def factory_metrics():
    """Get factory-level metrics"""
    try:
        metrics = get_factory_metrics()
        return jsonify(metrics), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/workers', methods=['GET'])
def workers_metrics():
    """Get metrics for all workers"""
    try:
        metrics = get_all_worker_metrics()
        return jsonify(metrics), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/workers/<worker_id>', methods=['GET'])
def worker_metrics(worker_id):
    """Get metrics for a specific worker"""
    try:
        metrics = get_worker_metrics(worker_id)
        if metrics:
            return jsonify(metrics), 200
        else:
            return jsonify({'error': 'Worker not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/workstations', methods=['GET'])
def workstations_metrics():
    """Get metrics for all workstations"""
    try:
        metrics = get_all_workstation_metrics()
        return jsonify(metrics), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/workstations/<station_id>', methods=['GET'])
def workstation_metrics(station_id):
    """Get metrics for a specific workstation"""
    try:
        metrics = get_workstation_metrics(station_id)
        if metrics:
            return jsonify(metrics), 200
        else:
            return jsonify({'error': 'Workstation not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
