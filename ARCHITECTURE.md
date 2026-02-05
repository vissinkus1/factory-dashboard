# Factory Productivity Dashboard - Architecture & Design Document

**Version:** 1.0.0  
**Date:** February 2026  
**Status:** Production-Ready  

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Technology Stack](#technology-stack)
3. [Data Flow](#data-flow)
4. [API Design](#api-design)
5. [Database Schema](#database-schema)
6. [Deployment Strategy](#deployment-strategy)
7. [Scaling Strategy](#scaling-strategy)
8. [Monitoring & Observability](#monitoring--observability)
9. [Security Architecture](#security-architecture)
10. [Performance Considerations](#performance-considerations)

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      EDGE LAYER                              │
│  CCTV Cameras with Computer Vision AI Detection              │
└────────────────────── │ ────────────────────────────────────┘
                        │ JSON Events
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    API GATEWAY / LB                          │
│  Load Balancer (NGINX/HAProxy) with Rate Limiting            │
└────────────────────── │ ────────────────────────────────────┘
                        │
              ┌─────────┴─────────┐
              │                   │
              ▼                   ▼
        ┌──────────────┐  ┌──────────────┐
        │   Backend    │  │   Backend    │
        │  Instance 1  │  │  Instance 2  │
        │              │  │              │
        │  Flask API   │  │  Flask API   │
        │  Port 5000   │  │  Port 5000   │
        └──────┬───────┘  └──────┬───────┘
               │                 │
               └────────┬────────┘
                        │
                        ▼
        ┌─────────────────────────────┐
        │   Shared Database Layer      │
        │   (PostgreSQL / SQLite)      │
        │   with Connection Pool       │
        └─────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
   ┌─────────┐   ┌──────────┐   ┌─────────────┐
   │  Cache  │   │  Metrics │   │     Logs    │
   │ (Redis) │   │(Prometheus) │ (ELK Stack) │
   └─────────┘   └──────────┘   └─────────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
              ┌─────────┴─────────┐
              │                   │
              ▼                   ▼
        ┌──────────────┐  ┌──────────────┐
        │  Dashboard   │  │  Admin UI    │
        │  Frontend    │  │  (Optional)  │
        │  Port 8080   │  │  Port 8081   │
        └──────────────┘  └──────────────┘
```

### Component Breakdown

| Component | Purpose | Technology | Scaling |
|-----------|---------|-----------|---------|
| **CCTV Systems** | Event source | Computer Vision (OpenCV/TensorFlow) | Edge deployment |
| **API Gateway** | Request routing, rate limiting | NGINX/HAProxy | Horizontal |
| **Backend Services** | Business logic, metrics computation | Flask + Flask-RESTX | Horizontal (via load balancer) |
| **Database** | Persistent event storage | PostgreSQL (prod) / SQLite (dev) | Vertical + Read Replicas |
| **Cache Layer** | Request caching, sessions | Redis | Horizontal |
| **Message Queue** | Async event processing | RabbitMQ/Kafka (Optional) | Horizontal |
| **Monitoring** | Performance tracking | Prometheus + Grafana | Centralized |
| **Logging** | Audit trail, debugging | ELK Stack / Loki | Centralized |

---

## Technology Stack

### Backend
- **Framework:** Flask 3.0+ with Flask-RESTX for API documentation
- **Python Version:** 3.10+
- **API Documentation:** Swagger/OpenAPI 3.0
- **Authentication:** JWT (JWT-Extended)
- **Validation:** Marshmallow schemas

### Frontend
- **Framework:** HTML5 + CSS3 + Vanilla JavaScript
- **Charts:** Chart.js or D3.js
- **HTTP Client:** Fetch API + Axios
- **Build Tool:** Webpack (optional)

### Database
- **Primary:** PostgreSQL 14+
- **Dev/Test:** SQLite 3
- **Connection Pooling:** SQLAlchemy + psycopg2
- **Migrations:** Alembic

### DevOps & Deployment
- **Containerization:** Docker + Docker Compose
- **Orchestration:** Kubernetes (optional)
- **CI/CD:** GitHub Actions
- **Registry:** GitHub Container Registry (GHCR)
- **IaC:** Terraform (optional)

### Monitoring & Observability
- **Metrics:** Prometheus
- **Visualization:** Grafana
- **Logging:** ELK Stack (Elasticsearch, Logstash, Kibana)
- **Tracing:** Jaeger (optional)
- **APM:** Datadog or New Relic (optional)

---

## Data Flow

### Event Ingestion Flow

```
CCTV System
    │
    ├─ Detection: Worker_114 is working at Station_3
    │
    ├─ Generate JSON Event
    │  {
    │    "timestamp": "2026-02-06T10:30:00Z",
    │    "worker_id": "W114",
    │    "workstation_id": "S3",
    │    "event_type": "working",
    │    "duration_seconds": 1800,
    │    "units_produced": 45
    │  }
    │
    ├─ POST /events/ via HTTP/REST
    │
    ├─ Flask API Receives Event
    │  ├─ Validate JSON schema
    │  ├─ Check required fields
    │  ├─ Verify worker/station exist
    │  └─ Log event (INFO level)
    │
    ├─ Store in Database
    │  └─ INSERT INTO events TABLE
    │
    ├─ Update Metrics Cache
    │  ├─ Increment worker utilization
    │  ├─ Increment station throughput
    │  └─ Update factory aggregates
    │
    └─ Return 201 Created Response
```

### Metrics Calculation Flow

```
Metrics Request
    │
    ├─ GET /metrics/workers/W114
    │
    ├─ Flask Handler Receives
    │
    ├─ Check Cache (Redis)
    │  ├─ If hit: Return cached data
    │  └─ If miss: Recalculate
    │
    ├─ Query Database
    │  ├─ SELECT * FROM events WHERE worker_id = 'W114'
    │  ├─ GROUP BY event_type
    │  └─ CALCULATE aggregates
    │
    ├─ Calculate Metrics
    │  ├─ Total working hours = SUM(duration) WHERE event_type='working'
    │  ├─ Total idle hours = SUM(duration) WHERE event_type='idle'
    │  ├─ Utilization % = working_hours / total_hours
    │  ├─ Units produced = SUM(units_produced)
    │  └─ Productivity rate = units / working_hours
    │
    ├─ Cache Result (5-minute TTL)
    │
    └─ Return 200 OK with JSON metrics
```

---

## API Design

### RESTful Principles

Our API follows REST principles:

| HTTP Method | Purpose | Idempotent |
|-------------|---------|-----------|
| GET | Retrieve data | Yes |
| POST | Create data | No |
| PUT | Replace data | Yes |
| DELETE | Remove data | Yes |
| PATCH | Partial update | No |

### API Versioning Strategy

- **Current Version:** v1.0.0
- **URL Structure:** `/api/v1/resource` (for future versions)
- **Deprecation:** 6-month grace period for old versions

### Error Handling

All error responses follow consistent format:

```json
{
  "error": "Detailed error message",
  "status": 400,
  "timestamp": "2026-02-06T10:30:00Z",
  "path": "/api/v1/events",
  "request_id": "req-12345-abcde"
}
```

### Rate Limiting

- **Limit:** 1000 requests per minute per IP
- **Header:** `X-RateLimit-Remaining`
- **Exceeded:** Return 429 Too Many Requests

---

## Database Schema

### Workers Table

```sql
CREATE TABLE workers (
    worker_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT,
    shift TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_workers_department ON workers(department);
CREATE INDEX idx_workers_shift ON workers(shift);
```

### Workstations Table

```sql
CREATE TABLE workstations (
    station_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT,
    capacity_per_hour INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stations_location ON workstations(location);
```

### Events Table

```sql
CREATE TABLE events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP NOT NULL,
    worker_id TEXT NOT NULL,
    workstation_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('working', 'idle', 'absent', 'product_count')),
    duration_seconds INTEGER,
    units_produced INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (worker_id) REFERENCES workers(worker_id),
    FOREIGN KEY (workstation_id) REFERENCES workstations(station_id)
);

CREATE INDEX idx_events_timestamp ON events(timestamp);
CREATE INDEX idx_events_worker_date ON events(worker_id, timestamp);
CREATE INDEX idx_events_station_date ON events(workstation_id, timestamp);
CREATE INDEX idx_events_type ON events(event_type);
```

### Indexing Strategy

- **Timestamp indexes:** Quick range queries for daily/hourly reports
- **Composite indexes:** Common filter combinations (worker+date)
- **Event type index:** Fast filtering by event category

---

## Deployment Strategy

### Development Environment

```bash
# Local setup
docker-compose up  # Uses docker-compose.yml
# Runs on:
# - Frontend: http://localhost:8080
# - Backend: http://localhost:5000
# - Database: SQLite (factory_dashboard.db)
```

### Staging Environment

```yaml
# Kubernetes deployment with:
- 2 backend replicas
- PostgreSQL with backup
- Redis cache
- Prometheus monitoring
```

### Production Environment

```yaml
# Multi-region deployment with:
- 3+ backend replicas (auto-scaling)
- PostgreSQL with read replicas
- Redis cluster
- Load balancing (NGINX)
- TLS/SSL encryption
- Centralized logging (ELK)
- Prometheus + Grafana monitoring
```

---

## Scaling Strategy

### Horizontal Scaling (Recommended)

1. **Backend Services:** Add more Flask instances behind load balancer
2. **Database Reads:** PostgreSQL read replicas for reporting
3. **Cache:** Redis cluster for distributed caching
4. **Message Queue:** Kafka for event streaming (future)

### Vertical Scaling

- Increase CPU/RAM for backend instances
- Database server specs increase
- Not recommended as primary strategy

### Database Optimization for Scale

```sql
-- Partitioning by date (for large databases)
CREATE TABLE events_2026_01 PARTITION OF events
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- Materialized views for pre-aggregated metrics
CREATE MATERIALIZED VIEW daily_metrics AS
SELECT
    DATE(timestamp) as date,
    worker_id,
    workstation_id,
    SUM(CASE WHEN event_type='working' THEN duration_seconds END) / 3600 as working_hours,
    SUM(units_produced) as total_units
FROM events
GROUP BY DATE(timestamp), worker_id, workstation_id;

CREATE INDEX ON daily_metrics(date, worker_id);
```

---

## Monitoring & Observability

### Key Metrics to Monitor

**System Metrics:**
- Backend CPU usage (alert if > 80%)
- Memory usage (alert if > 85%)
- Disk I/O (alert if > 90%)
- Database connections (alert if > 80% of pool)

**Application Metrics:**
- Request latency (p50, p95, p99)
- Error rate (alert if > 1%)
- Event ingestion rate (events/sec)
- API response times by endpoint

**Business Metrics:**
- Total events ingested (daily)
- Worker utilization percentage
- Production throughput
- System availability/uptime

### Prometheus Configuration

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'flask_app'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:6379']
```

### Grafana Dashboards

1. **System Health Dashboard**
   - CPU, Memory, Disk usage
   - Network I/O
   - Database connections

2. **Application Performance Dashboard**
   - Request latency (by endpoint)
   - Error rates
   - Throughput

3. **Business Metrics Dashboard**
   - Worker utilization trends
   - Productivity metrics
   - Production targets tracking

---

## Security Architecture

### Authentication & Authorization

```
Public Endpoints:
├─ GET /health          (health check)
├─ GET /health/ready    (readiness probe)
└─ POST /events         (event ingestion - may need API key)

Protected Endpoints (require JWT):
├─ GET /metrics/*       (access control by role)
├─ DELETE /events/*     (admin only)
└─ POST /seed           (admin only)
```

### Data Security

1. **Encryption in Transit:** TLS 1.2+ for all HTTP
2. **Encryption at Rest:** Database column-level encryption for sensitive data
3. **Database:** User role separation in PostgreSQL
4. **Secrets Management:** Use environment variables, not hardcoded values

### API Security

```python
# Request Validation
@app.before_request
def validate_request():
    - Check JSON schema
    - Validate content-type
    - Rate limiting check
    - CORS validation

# Response Headers
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
```

---

## Performance Considerations

### Database Query Optimization

```sql
-- Use EXPLAIN ANALYZE to find slow queries
EXPLAIN ANALYZE
SELECT worker_id, SUM(units_produced)
FROM events
WHERE timestamp BETWEEN '2026-01-01' AND '2026-02-06'
GROUP BY worker_id;

-- Add indexes based on query patterns
CREATE INDEX idx_events_ts_worker ON events(timestamp, worker_id);
```

### Caching Strategy

```python
# 1. Query Result Caching (Redis)
@cache.cached(timeout=300, key_prefix='worker_metrics_')
def get_worker_metrics(worker_id):
    return calculate_metrics(worker_id)

# 2. Database-level Materialized Views
SELECT * FROM daily_metrics;

# 3. Application-level In-Memory Cache
```

### Connection Pooling

```python
# SQLAlchemy with connection pool
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,           # Number of connections to keep
    max_overflow=10,        # Additional connections allowed
    pool_timeout=30,        # Wait 30s for connection
    pool_recycle=3600       # Recycle connections every hour
)
```

---

## Future Enhancements

### Planned Features (v2.0)

1. **Machine Learning Integration**
   - Anomaly detection in worker behavior
   - Predictive maintenance for equipment
   - Demand forecasting

2. **Real-time Features**
   - WebSocket support for live metrics
   - Server-sent events (SSE)
   - Live dashboard updates

3. **Advanced Analytics**
   - Time-series forecasting
   - Comparative analysis (worker vs worker)
   - Trend analysis with alerts

4. **Multi-tenancy**
   - Support multiple factories
   - Organization isolation
   - Shared infrastructure

5. **Mobile Application**
   - Mobile dashboard
   - Push notifications
   - Offline data collection

---

## Maintenance & Support

### Regular Tasks

| Task | Frequency | Owner |
|------|-----------|-------|
| Database backup | Daily | DevOps |
| Log rotation | Weekly | Infrastructure |
| Security patches | As needed | Security team |
| Performance tuning | Monthly | Database admin |
| Capacity planning | Quarterly | Infrastructure |

### Disaster Recovery

- **RTO:** 1 hour (Recovery Time Objective)
- **RPO:** 15 minutes (Recovery Point Objective)
- **Backup:** Daily full + hourly incremental
- **Testing:** Monthly DR drill

---

## Conclusion

This architecture is designed to be:
- **Scalable:** Horizontal scaling of all components
- **Reliable:** Redundancy and failover mechanisms
- **Observable:** Comprehensive monitoring and logging
- **Secure:** Defense-in-depth approach
- **Maintainable:** Clear separation of concerns

For questions or updates, contact the engineering team.

---

**Document History:**
- v1.0.0 - Initial release (Feb 2026)
