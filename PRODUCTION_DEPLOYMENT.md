# Production Deployment Guide

**Version:** 1.0.0  
**Last Updated:** February 2026

---

## Quick Start Checklist

- [ ] Clone repository
- [ ] Configure environment variables  
- [ ] Setup database
- [ ] Configure SSL certificates
- [ ] Setup monitoring tools
- [ ] Configure backups
- [ ] Run security scans
- [ ] Load test
- [ ] Deploy to staging
- [ ] User acceptance testing (UAT)
- [ ] Deploy to production
- [ ] Verify health checks
- [ ] Monitor metrics

---

## Pre-Deployment Checklist

### 1. Requirements Verification

```bash
# System Requirements
- Ubuntu 20.04 LTS or later
- Docker 20.10+
- Docker Compose 2.0+
- Python 3.10+ (if deploying without containers)
- PostgreSQL 14+ (production database)
- Redis 6.0+ (optional, for caching)
- Minimum 2 CPU cores, 4GB RAM
```

### 2. Security Audit

```bash
# Run security checks
cd Factory\ dashboard

# Dependency vulnerability scan
pip install bandit safety
bandit -r backend/ -f json
safety check --json

# Database security review
- Verify all secrets in environment variables
- Review database user permissions
- Confirm TLS connections to database
- Check VPC network policies

# Application security
- Review Flask security headers
- Verify CORS configuration
- Check authentication mechanisms
- Review API rate limiting
```

### 3. Infrastructure Preparation

```bash
# DNS Configuration
factory-dashboard.yourdomain.com  →  Your Load Balancer IP

# SSL/TLS Certificates
# Option 1: Let's Encrypt (Recommended)
certbot certonly --standalone -d factory-dashboard.yourdomain.com

# Option 2: Commercial certificate
# Upload your certificate files to /etc/ssl/certs/

# Directory Structure
/opt/factory-dashboard/
├── app/
├── data/
├── logs/
├── backup/
└── config/
```

---

## Environment Configuration

### 1. Create Production .env File

```bash
# Copy template and customize
cp .env.example .env

# Edit .env with production values
nano .env
```

### 2. Key Environment Variables

```bash
# APPLICATION
APP_ENV=production
DEBUG=False
FLASK_SECRET_KEY=$(openssl rand -base64 32)  # Generate secure key

# DATABASE - PostgreSQL
DB_TYPE=postgresql
DB_HOST=db.internal.yourdomain.com
DB_PORT=5432
DB_NAME=factory_prod
DB_USER=app_user
DB_PASSWORD=$(openssl rand -base64 32)

# REDIS
REDIS_ENABLED=True
REDIS_HOST=redis.internal.yourdomain.com
REDIS_PORT=6379
REDIS_DB=0

# SECURITY
REQUIRE_HTTPS=True
JWT_SECRET_KEY=$(openssl rand -base64 32)
CORS_ORIGINS=https://factory-dashboard.yourdomain.com

# LOGGING
LOG_LEVEL=INFO
LOG_FILE=/var/log/factory-dashboard/app.log

# MONITORING
ENABLE_METRICS=True
METRICS_PORT=8001
```

### 3. Validate Configuration

```bash
# Test database connection
python backend/test_connection.py

# Verify all required variables
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('DB_HOST'))"
```

---

## Database Setup

### 1. PostgreSQL Installation

```bash
# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib libpq-dev

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create user and database
sudo -u postgres psql << EOF
CREATE USER app_user WITH PASSWORD 'secure_password';
CREATE DATABASE factory_prod OWNER app_user;
ALTER DATABASE factory_prod SET timezone TO 'UTC';
GRANT ALL ON SCHEMA public TO app_user;
EOF

# Verify
psql -h localhost -U app_user -d factory_prod -c "SELECT version();"
```

### 2. Initialize Database Schema

```bash
# Run migrations
cd backend
python -c "from database import init_db; init_db()"

# Seed initial data (optional)
python -c "from database import seed_database; seed_database()"

# Verify tables
psql -h localhost -U app_user -d factory_prod << EOF
\dt
\d events
EOF
```

### 3. Database Backup Configuration

```bash
# Create backup script: /opt/factory-dashboard/backup.sh
#!/bin/bash
BACKUP_DIR="/opt/factory-dashboard/backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="factory_prod"
DB_USER="app_user"
DB_HOST="localhost"

# Full backup
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME | gzip > "$BACKUP_DIR/factory_$TIMESTAMP.sql.gz"

# Keep only last 30 days
find $BACKUP_DIR -name "factory_*.sql.gz" -mtime +30 -delete

echo "Backup completed: factory_$TIMESTAMP.sql.gz"

# Create cronjob
# 0 2 * * * /opt/factory-dashboard/backup.sh  # Daily at 2 AM
```

---

## Docker Deployment

### 1. Build Docker Images

```bash
# Build backend image
docker build -f Dockerfile.backend \
  -t factory-dashboard-backend:latest \
  -t factory-dashboard-backend:1.0.0 \
  .

# Build frontend image
docker build -f Dockerfile.frontend \
  -t factory-dashboard-frontend:latest \
  -t factory-dashboard-frontend:1.0.0 \
  frontend/

# Tag for registry
docker tag factory-dashboard-backend:latest ghcr.io/myorg/factory-dashboard-backend:latest
docker tag factory-dashboard-frontend:latest ghcr.io/myorg/factory-dashboard-frontend:latest

# Push to registry
docker login ghcr.io
docker push ghcr.io/myorg/factory-dashboard-backend:latest
docker push ghcr.io/myorg/factory-dashboard-frontend:latest
```

### 2. Docker Compose for Production

```yaml
version: '3.8'

services:
  backend:
    image: ghcr.io/myorg/factory-dashboard-backend:latest
    container_name: factory-backend
    environment:
      - DB_HOST=postgres
      - REDIS_HOST=redis
      - APP_ENV=production
    ports:
      - "5000:5000"
    depends_on:
      - postgres
      - redis
    restart: always
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    image: ghcr.io/myorg/factory-dashboard-frontend:latest
    container_name: factory-frontend
    ports:
      - "8080:8080"
    restart: always
    depends_on:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/index.html"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15-alpine
    container_name: factory-postgres
    environment:
      POSTGRES_DB: factory_prod
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backup:/backup
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app_user -d factory_prod"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: factory-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: always
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  prometheus:
    image: prom/prometheus:latest
    container_name: factory-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    restart: always

  grafana:
    image: grafana/grafana:latest
    container_name: factory-grafana
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana_data:/var/lib/grafana
    restart: always

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

### 3. Deploy with Docker Compose

```bash
# Pull latest images
docker-compose pull

# Start services
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Run migrations
docker-compose exec backend python -c "from database import init_db; init_db()"

# Stop services
docker-compose down
```

---

## NGINX Reverse Proxy Configuration

### 1. Install NGINX

```bash
sudo apt-get install nginx

# Enable service
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 2. Configure NGINX

```nginx
# /etc/nginx/sites-available/factory-dashboard

upstream backend {
    least_conn;
    server backend-1:5000;
    server backend-2:5000;
    server backend-3:5000;
}

server {
    listen 80;
    server_name factory-dashboard.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name factory-dashboard.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/certs/factory-dashboard.crt;
    ssl_certificate_key /etc/ssl/private/factory-dashboard.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Logging
    access_log /var/log/nginx/factory-access.log combined;
    error_log /var/log/nginx/factory-error.log warn;
    
    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
    gzip_min_length 1000;
    
    # Frontend
    location / {
        proxy_pass http://frontend:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # API Backend
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_request_buffering off;
    }
    
    # API Documentation
    location /docs {
        proxy_pass http://backend/docs;
        proxy_set_header Host $host;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://backend/health;
        access_log off;
    }
}
```

### 3. Enable Configuration

```bash
# Test syntax
sudo nginx -t

# Enable site
sudo ln -s /etc/nginx/sites-available/factory-dashboard \
  /etc/nginx/sites-enabled/

# Reload NGINX
sudo systemctl reload nginx
```

---

## Monitoring Setup

### 1. Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'prod'
    environment: 'production'

scrape_configs:
  - job_name: 'factory-api'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['backend:5000']
    scrape_interval: 10s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

# Alert rules
rule_files:
  - 'alerts.yml'
```

### 2. Alert Rules

```yaml
# alerts.yml
groups:
  - name: factory_dashboard
    rules:
      - alert: BackendDown
        expr: up{job="factory-api"} == 0
        for: 5m
        annotations:
          summary: "Backend service is down"
          
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 10m
        annotations:
          summary: "High error rate detected"
          
      - alert: SlowRequests
        expr: histogram_quantile(0.99, http_request_duration_seconds) > 1
        for: 5m
        annotations:
          summary: "Slow requests detected"
```

### 3. Grafana Dashboards

Access at: `http://localhost:3000`
- Default login: `admin:admin`
- Configure data source pointing to Prometheus
- Import sample dashboards from `monitoring/dashboards/`

---

## Health Checks & Monitoring

### 1. Verify Deployment

```bash
# Check all services are running
docker ps

# Test health endpoints
curl https://factory-dashboard.yourdomain.com/health
curl https://factory-dashboard.yourdomain.com/health/ready

# Check database connectivity
docker-compose exec backend python -c "from database import get_workers; print(len(get_workers()))"

# Verify API endpoints
curl https://factory-dashboard.yourdomain.com/api/workers
curl https://factory-dashboard.yourdomain.com/api/metrics/factory

# Check frontend
curl https://factory-dashboard.yourdomain.com/
```

### 2. Log Monitoring

```bash
# Tail application logs
docker-compose logs -f backend

# Filter for errors
docker-compose logs backend 2>&1 | grep -i error

# Check NGINX logs
tail -f /var/log/nginx/factory-access.log
```

---

## Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Run load test
ab -n 10000 -c 100 -H "Content-Type: application/json" \
  https://factory-dashboard.yourdomain.com/health

# Test event ingestion
ab -n 1000 -c 50 -p event.json -T application/json \
  https://factory-dashboard.yourdomain.com/api/events
```

---

## Troubleshooting

### Issue: Database Connection Fails

```bash
# Check database logs
docker-compose logs postgres

# Verify credentials
docker-compose exec postgres psql -U app_user -d factory_prod

# Check network connectivity
docker-compose exec backend ping postgres
```

### Issue: High Memory Usage

```bash
# Check resource limits
docker stats

# Increase database connection pool size
# In backend env: DB_POOL_SIZE=25

# Restart service
docker-compose restart backend
```

### Issue: Slow Queries

```bash
# Enable PostgreSQL query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();

# Analyze query performance
EXPLAIN ANALYZE SELECT * FROM events ...;

# Add missing indexes
CREATE INDEX idx_events_date ON events(DATE(timestamp));
```

---

## Maintenance Tasks

| Task | Frequency | Command |
|------|-----------|---------|
| Database backup | Daily | `./backup.sh` |
| Log rotation | Weekly | `docker-compose logs --follow` |
| SSL cert renewal | Quarterly | `certbot renew` |
| Dependency updates | Monthly | `docker-compose pull &&docker-compose up -d` |
| Performance tuning | Quarterly | Review Grafana metrics |

---

## Rollback Procedure

If deployment fails:

```bash
# View deployment history
docker image ls | grep factory-dashboard

# Rollback to previous version
docker-compose down
docker pull ghcr.io/myorg/factory-dashboard-backend:1.0.0
sed -i 's/latest/1.0.0/g' docker-compose.yml
docker-compose up -d

# Verify rollback
curl https://factory-dashboard.yourdomain.com/health
```

---

## Support & Escalation

For issues:
1. Check monitoring dashboards (Prometheus/Grafana)
2. Review application logs
3. Check database status
4. Open GitHub issue with logs

---

**Next Steps:**
- [ ] Configure SSL certificates
- [ ] Setup monitoring dashboards
- [ ] Run load tests
- [ ] Document custom configurations
- [ ] Train support team
- [ ] Schedule first backup test
