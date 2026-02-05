# Factory Productivity Dashboard

An AI-powered worker productivity monitoring system that ingests computer vision events from CCTV cameras and displays real-time productivity metrics in an interactive web dashboard.

## Live Demo

**🚀 Deployed Application:** https://web-production-e5d00.up.railway.app

### Quick Links
- **Dashboard**: https://web-production-e5d00.up.railway.app
- **API Documentation (Swagger)**: https://web-production-e5d00.up.railway.app/docs
- **GitHub Repository**: https://github.com/vissinkus1/factory-dashboard

## Project Overview

This full-stack web application monitors worker activity and workstation utilization in a manufacturing factory. It processes AI-generated events from computer vision systems, computes productivity metrics, and displays them through an intuitive dashboard.

### Key Features

- **Real-time Event Ingestion**: Accept and process AI-generated events from CCTV systems
- **Comprehensive Metrics**: Compute worker, workstation, and factory-level productivity metrics
- **Interactive Dashboard**: View live productivity data with filtering and drill-down capabilities
- **RESTful API**: Complete set of APIs for ingestion and metrics retrieval
- **Docker Support**: Containerized full-stack deployment
- **Production-Ready**: Handles edge cases and includes error handling

## Architecture

### Edge → Backend → Dashboard Flow

```
┌─────────────────────┐
│  CCTV Cameras       │
│  (Computer Vision)  │
│                     │
│ Events:             │
│ - working           │
│ - idle              │
│ - absent            │
│ - product_count     │
└──────────┬──────────┘
           │
           ↓
┌──────────────────────────┐
│  Backend API             │
│  (Flask)                 │
│                          │
│ /api/events (POST)       │
│ /api/metrics/* (GET)     │
│ /api/seed (POST)         │
└──────────┬───────────────┘
           │
           ↓
┌──────────────────────────┐
│  SQLite Database         │
│                          │
│ Tables:                  │
│ - workers                │
│ - workstations           │
│ - events                 │
└──────────┬───────────────┘
           │
           ↓
┌──────────────────────────┐
│  Frontend Dashboard      │
│  (HTML/CSS/JavaScript)   │
│                          │
│ - Factory Summary        │
│ - Worker Metrics Table   │
│ - Station Metrics Table  │
└──────────────────────────┘
```

### System Components

1. **Backend API Server** (`backend/app.py`)
   - Flask-based REST API
   - CORS enabled for cross-origin requests
   - Database operations and metric calculations
   - Event ingestion endpoints

2. **Database Layer** (`backend/database.py`)
   - SQLite database management
   - Schema initialization
   - CRUD operations
   - Metric computation logic

3. **Frontend Dashboard** (`frontend/index.html`)
   - Single-page application
   - Real-time data refresh
   - Responsive design
   - Filter and drill-down capabilities

4. **Containerization**
   - Docker Compose orchestration
   - Isolated backend and frontend services
   - Network communication between services

## Database Schema

### workers
```
- worker_id (TEXT, PRIMARY KEY): Unique worker identifier
- name (TEXT): Worker's name
- created_at (TIMESTAMP): Record creation time
```

### workstations
```
- station_id (TEXT, PRIMARY KEY): Unique workstation identifier
- name (TEXT): Workstation name
- type (TEXT): Workstation type (assembly, inspection, packaging, etc.)
- created_at (TIMESTAMP): Record creation time
```

### events
```
- event_id (INTEGER, PRIMARY KEY): Unique event identifier
- timestamp (TIMESTAMP): When the event occurred (ISO 8601)
- worker_id (TEXT, FOREIGN KEY): Reference to worker
- station_id (TEXT, FOREIGN KEY): Reference to workstation
- event_type (TEXT): Type of event (working, idle, absent, product_count)
- confidence (REAL): Confidence score from CV model (0.0-1.0)
- count (INTEGER): Number of units (for product_count events)
- created_at (TIMESTAMP): Record creation time
```

### Indexes
- `idx_events_timestamp`: Speeds up time-range queries
- `idx_events_worker_id`: Speeds up worker queries
- `idx_events_station_id`: Speeds up workstation queries
- `idx_events_event_type`: Speeds up event-type filtering

## Metrics Definitions

### Worker-Level Metrics

- **Total Active Time**: Sum of durations between consecutive events of type "working"
  - Calculation: For each working event, measure duration until next event
  - Unit: Hours

- **Total Idle Time**: Sum of durations between consecutive events of type "idle"
  - Calculation: For each idle event, measure duration until next event
  - Unit: Hours

- **Utilization Percentage**: (Active Time) / (Active Time + Idle Time) × 100
  - Represents percentage of time worker is productive vs. idle
  - Range: 0-100%

- **Total Units Produced**: Sum of all `count` values in product_count events
  - Only product_count events contribute
  - Unit: Number of units

- **Units Per Hour**: Total Units Produced / Total Active Time
  - Productivity rate during active work periods
  - Unit: Units per hour

### Workstation-Level Metrics

- **Occupancy Time**: Sum of durations when workstation has any worker activity
  - Calculation: Measure duration from first event to last event during work periods
  - Unit: Hours

- **Utilization Percentage**: Percentage of available working hours the station is in use
  - Currently computed as weighted average of events
  - Range: 0-100%

- **Total Units Produced**: Sum of all `count` values in product_count events at that station
  - Unit: Number of units

- **Throughput Rate**: Total Units Produced / Occupancy Time
  - Rate of production when station is occupied
  - Unit: Units per hour

### Factory-Level Metrics

- **Total Productive Time**: Sum of all worker active times across all workers
  - Calculation: Aggregate all working event durations
  - Unit: Hours

- **Total Production Count**: Sum of all units produced across all workers and stations
  - Calculation: Sum of all product_count event values
  - Unit: Number of units

- **Average Production Rate**: Total Production Count / Total Productive Time
  - Overall factory productivity
  - Unit: Units per hour

- **Average Utilization**: Average of all worker utilization percentages
  - Overall factory efficiency
  - Range: 0-100%

## Key Assumptions

### Time Calculation
1. **Event Duration**: The duration of an event is calculated as the time difference between the current event timestamp and the next event timestamp
2. **Shift Coverage**: Data includes 8-hour shifts (8 AM - 5 PM) with sample data for multiple days
3. **Continuous Activity**: Events must have clear before/after relationships for duration calculations

### Event Processing
1. **No Deduplication**: Events are inserted as-is; duplicate detection is implemented via unique constraints if needed
2. **Out-of-Order Handling**: Events are sorted by timestamp during metric calculation
3. **Confidence Scores**: Used for filtering in advanced implementations; currently all events are processed

### Data Assumptions
1. **Worker-Station Mapping**: Workers are assigned to specific workstations; they may work at different stations across shifts
2. **Product Count Timing**: product_count events mark completed units; they may occur during or after working events
3. **Idle Events**: Indicate periods when worker is at station but not actively working (breaks, waiting for materials)
4. **Absent Events**: Mark periods when worker is not at any station (not currently used in demo)

### Factory Setup
- Fixed 6 workers and 6 workstations
- Hardcoded metadata for workers and stations
- Sample data spans 2 days with realistic event patterns

## API Documentation

### Base URL
```
http://localhost:5000/api
```

### Endpoints

#### Health Check
```
GET /health
Response: { "status": "healthy" }
```

#### Seed Database
```
POST /api/seed
Response: { "message": "Database seeded successfully" }
```

#### Get Workers
```
GET /api/workers
Response: [
  { "worker_id": "W1", "name": "Alice Johnson" },
  ...
]
```

#### Get Workstations
```
GET /api/workstations
Response: [
  { "station_id": "S1", "name": "Assembly Line 1", "type": "assembly" },
  ...
]
```

#### Ingest Single Event
```
POST /api/events
Content-Type: application/json

{
  "timestamp": "2026-01-15T10:15:00Z",
  "worker_id": "W1",
  "workstation_id": "S3",
  "event_type": "working",
  "confidence": 0.93,
  "count": 1
}

Response: { "message": "Event ingested successfully" }
```

#### Ingest Batch Events
```
POST /api/events/batch
Content-Type: application/json

[
  { ... event 1 ... },
  { ... event 2 ... },
  ...
]

Response: {
  "message": "5/5 events ingested successfully",
  "success_count": 5,
  "total_count": 5
}
```

#### Get Factory Metrics
```
GET /api/metrics/factory
Response: {
  "total_productive_time_hours": 96.5,
  "total_production_count": 1245,
  "average_production_rate": 12.9,
  "average_utilization_percentage": 87.3,
  "worker_count": 6,
  "station_count": 6,
  "total_events": 432
}
```

#### Get All Worker Metrics
```
GET /api/metrics/workers
Response: [
  {
    "worker_id": "W1",
    "name": "Alice Johnson",
    "total_active_time_hours": 16.2,
    "total_idle_time_hours": 2.1,
    "utilization_percentage": 88.5,
    "total_units_produced": 195,
    "units_per_hour": 12.04,
    "event_count": 72
  },
  ...
]
```

#### Get Specific Worker Metrics
```
GET /api/metrics/workers/<worker_id>
Response: { ... worker metrics ... }
```

#### Get All Workstation Metrics
```
GET /api/metrics/workstations
Response: [
  {
    "station_id": "S1",
    "name": "Assembly Line 1",
    "type": "assembly",
    "occupancy_time_hours": 32.5,
    "utilization_percentage": 85.0,
    "total_units_produced": 325,
    "throughput_rate": 10.0,
    "event_count": 72
  },
  ...
]
```

#### Get Specific Workstation Metrics
```
GET /api/metrics/workstations/<station_id>
Response: { ... workstation metrics ... }
```

## Running the Application

### Prerequisites
- Docker and Docker Compose, OR
- Python 3.10+ with Flask
- Node.js 18+ for frontend server

### Using Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   cd dashnoard
   ```

2. **Build and start services**
   ```bash
   docker-compose up --build
   ```

3. **Access the dashboard**
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:5000

4. **Stop services**
   ```bash
   docker-compose down
   ```

### Manual Setup (Without Docker)

1. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   python app.py
   ```

2. **Frontend Setup** (in another terminal)
   ```bash
   cd frontend
   python -m http.server 8080
   ```

3. **Access the dashboard**
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:5000

## Handling Edge Cases

### Intermittent Connectivity

**Problem**: Events may fail to be delivered if CCTV system loses connection to API.

**Solution**:
1. **Client-Side Buffering**: CCTV system maintains local queue of events
2. **Retry Logic**: Implement exponential backoff for failed POSTs
3. **Batch Submission**: Use `/api/events/batch` to submit accumulated events when connection restored
4. **Idempotency**: Include event_id in request; server deduplicates via unique constraint

**Implementation**:
```python
# Example client-side retry logic
async def send_events_with_retry(events, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = await post('/api/events/batch', events)
            return response
        except ConnectionError:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
```

### Duplicate Events

**Problem**: Retries or network issues may result in the same event being submitted multiple times.

**Solution**:
1. **Content-Hash Deduplication**: Create unique hash of (timestamp, worker_id, station_id, event_type)
2. **Database Constraint**: Add unique constraint on this tuple
3. **Time Window**: Events within same second from same worker at same station are flagged as potential duplicates

**Implementation**:
```python
# Add unique constraint in schema
CREATE UNIQUE INDEX idx_events_dedup ON events(timestamp, worker_id, station_id, event_type)
```

### Out-of-Order Timestamps

**Problem**: Events may arrive out of chronological order due to network latency or processing delays.

**Solution**:
1. **Timestamp Sorting**: Always sort events by timestamp before metric calculation
2. **Received Timestamp**: Track both event timestamp (when it occurred) and received timestamp
3. **Window-Based Aggregation**: Group events into 5-minute or hourly windows to smooth out ordering

**Implementation**:
```python
# In metric calculations, always sort first
cursor.execute('''
    SELECT * FROM events 
    WHERE worker_id = ? 
    ORDER BY timestamp ASC
''', (worker_id,))
```

## Scaling Considerations

### From 5 Cameras → 100+ Cameras

**Current Bottlenecks**:
- Single SQLite database has write limitations
- In-memory metric calculations don't scale
- Single Flask worker thread

**Scaling Strategy**:

1. **Database Migration**
   - Move from SQLite to PostgreSQL or MySQL
   - Benefits: Better concurrency, replication, indexing
   - Implementation: Minimal code changes; use SQLAlchemy ORM

2. **Distributed Event Processing**
   ```
   CCTV Systems → Message Queue (Kafka/RabbitMQ) → Workers → Database
   ```
   - Decouples ingestion from processing
   - Allows parallel event processing
   - Enables backpressure handling

3. **Caching Layer**
   ```
   Applications → Redis Cache → PostgreSQL
   ```
   - Cache frequently accessed metrics
   - Reduce database load
   - Implement time-based TTL (5-minute refresh)

4. **Horizontal Scaling**
   - Multiple Flask instances behind load balancer (Nginx)
   - Each instance connects to shared database
   - Stateless design allows easy scaling

### From Single Site → Multi-Site

**Architecture**:
```
Site 1 CCTV → ┐
Site 2 CCTV → ├→ Central Message Queue → Processing Workers → Global Database
Site 3 CCTV → ┘

Frontend → Site-Aggregated Dashboard
```

**Implementation**:
1. **Add Site ID to Schema**
   ```sql
   ALTER TABLE events ADD COLUMN site_id TEXT;
   ALTER TABLE workers ADD COLUMN site_id TEXT;
   ALTER TABLE workstations ADD COLUMN site_id TEXT;
   ```

2. **Multi-Tenancy Support**
   - Filter queries by site_id
   - Per-site metric aggregation
   - Per-site data retention policies

3. **Global Dashboard**
   - Aggregate metrics across sites
   - Site-level comparison
   - Unified reporting

4. **Data Federation**
   - Option 1: Replicate all data to central warehouse
   - Option 2: Query each site's database in parallel

### Performance Optimizations

**For 100+ Cameras at 30 FPS** (3,000 events/second):

1. **Batch Ingestion**
   ```python
   # Reduce transaction overhead
   cursor.executemany(..., batch_size=1000)
   ```

2. **Materialized Views**
   ```sql
   -- Pre-compute hourly aggregates
   CREATE MATERIALIZED VIEW hourly_metrics AS
   SELECT worker_id, DATE_TRUNC('hour', timestamp) as hour,
          COUNT(*) as event_count
   FROM events
   GROUP BY worker_id, hour;
   ```

3. **Partitioning**
   ```sql
   -- Partition events by date for faster queries
   CREATE TABLE events_2026_01 PARTITION OF events
   FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
   ```

4. **Asynchronous Processing**
   ```python
   # Use Celery for background tasks
   @celery.task
   def compute_metrics_async(worker_id):
       # Long-running calculation
       return get_worker_metrics(worker_id)
   ```

## ML Model Management

### Adding Model Versioning

**Problem**: Computer vision models improve over time; old vs. new event confidence needs tracking.

**Solution**:

1. **Add Model Metadata to Schema**
   ```sql
   CREATE TABLE cv_models (
       model_id INTEGER PRIMARY KEY,
       model_name TEXT,
       version TEXT,
       deployed_at TIMESTAMP,
       status TEXT
   );

   ALTER TABLE events ADD COLUMN model_id INTEGER REFERENCES cv_models(model_id);
   ```

2. **Track Model Information**
   - CCTV system sends model_version in event
   - Backend stores and associates model_id with events
   - Enables comparison between model versions

3. **Query by Model Version**
   ```python
   def get_metrics_for_model_version(worker_id, model_version):
       cursor.execute('''
           SELECT * FROM events 
           WHERE worker_id = ? AND model_id = ?
           ORDER BY timestamp
       ''', (worker_id, model_version))
   ```

### Detecting Model Drift

**Problem**: CV model performance degrades over time without detection.

**Detection Strategy**:

1. **Statistical Monitoring**
   ```python
   # Monitor confidence score distribution
   def detect_drift(worker_id, window_days=7):
       # Get metrics for past 30 days
       recent = get_events(worker_id, days=7)
       historical = get_events(worker_id, days=30)
       
       # Compare confidence score distribution
       recent_avg_conf = mean([e['confidence'] for e in recent])
       historical_avg_conf = mean([e['confidence'] for e in historical])
       
       # Flag if > 10% drop
       if (historical_avg_conf - recent_avg_conf) / historical_avg_conf > 0.1:
           return "DRIFT_DETECTED"
   ```

2. **Behavioral Anomalies**
   ```python
   # Compare current metrics to historical baseline
   def detect_anomalies(worker_id):
       current = get_worker_metrics(worker_id)
       historical_avg = get_historical_average(worker_id)
       
       # Flag if productivity drops unexpectedly
       if current['utilization_percentage'] < historical_avg * 0.75:
           return "ANOMALY_DETECTED"
   ```

3. **Dashboard Alert**
   - Add metrics comparison section
   - Show model confidence trends over time
   - Alert when drift threshold exceeded

### Triggering Retraining

**Workflow**:

```
Drift Detected
    ↓
Alert Data Science Team
    ↓
Review Recent Events (Confidence < 0.8)
    ↓
Collect Labeled Data
    ↓
Retrain Model
    ↓
Test on Holdout Set
    ↓
Deploy New Version
    ↓
Update Events with new_model_id
    ↓
Monitor New Model Performance
```

**Implementation**:
```python
@app.route('/api/models/trigger-retrain', methods=['POST'])
def trigger_retrain():
    """Signal to ML pipeline that retraining needed"""
    recent_events = get_low_confidence_events(days=7, threshold=0.8)
    
    # Send to retraining pipeline (Airflow, Kubeflow, etc.)
    pipeline.submit_job({
        'event_ids': [e['event_id'] for e in recent_events],
        'trigger_reason': 'DRIFT_DETECTED'
    })
    
    return {'status': 'Retraining triggered'}
```

## Technology Stack

- **Backend**: Flask 2.3.2, Python 3.10+
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Database**: SQLite (production would use PostgreSQL)
- **Containerization**: Docker, Docker Compose
- **HTTP Server**: Python http.server, Node.js http-server

## Project Structure

```
dashnoard/
├── backend/
│   ├── app.py              # Flask API server
│   ├── database.py         # Database layer
│   └── requirements.txt     # Python dependencies
├── frontend/
│   └── index.html          # Dashboard UI
├── database/
│   └── schema.sql          # Database schema
├── Dockerfile.backend      # Backend container
├── Dockerfile.frontend     # Frontend container
├── docker-compose.yml      # Multi-container orchestration
└── README.md               # This file
```

## Future Enhancements

1. **Authentication & Authorization**
   - Role-based access control (RBAC)
   - API key management for CCTV systems

2. **Real-Time Streaming**
   - WebSocket support for live metric updates
   - Server-Sent Events (SSE) for push notifications

3. **Advanced Analytics**
   - Trend analysis and forecasting
   - Anomaly detection using isolation forests
   - Worker performance ranking

4. **Integration**
   - ERP system integration for production targets
   - Slack/Teams notifications for alerts
   - Export to BI tools (Tableau, Power BI)

5. **Data Retention**
   - Implement data archival strategies
   - GDPR compliance for worker data
   - Configurable retention policies

## Troubleshooting

### Database Lock Errors
- **Cause**: Multiple writers to SQLite
- **Solution**: Switch to PostgreSQL for concurrent writes

### CORS Errors
- **Cause**: Frontend and backend on different origins
- **Solution**: Flask-CORS is enabled; check browser console

### Event Ingestion Failures
- **Cause**: Missing required fields or invalid event_type
- **Solution**: Validate event JSON against schema before POSTing

### Metrics Not Updating
- **Cause**: Events without proper timestamps or ordering
- **Solution**: Ensure timestamps are ISO 8601 format; check event ordering

## License

This project is provided as a technical assessment demonstration.

## Contact

For questions or support, contact the development team.
