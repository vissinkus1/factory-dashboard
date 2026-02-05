# Deployment Guide

## Quick Start with Docker Compose

### Prerequisites
- Docker (version 20.10+)
- Docker Compose (version 1.29+)

### Steps

1. **Clone/Download the project**
   ```bash
   cd dashnoard
   ```

2. **Build and start all services**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - Frontend Dashboard: http://localhost:8080
   - Backend API: http://localhost:5000/health
   - API Documentation: See README.md

4. **Initialize with dummy data**
   - Click "Reset with Dummy Data" button in the dashboard, OR
   - Make a POST request to http://localhost:5000/api/seed

5. **Stop the services**
   ```bash
   docker-compose down
   ```

---

## Local Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend server)
- Git

### Backend Setup

1. **Install Python dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Start the Flask server**
   ```bash
   python app.py
   ```
   
   The server will start on http://localhost:5000

### Frontend Setup (in a new terminal)

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Start a local HTTP server**
   
   **Option A: Using Python**
   ```bash
   python -m http.server 8080
   ```
   
   **Option B: Using Node.js**
   ```bash
   npm install -g http-server
   http-server -p 8080
   ```
   
   **Option C: Using Node.js with npx**
   ```bash
   npx http-server -p 8080
   ```

3. **Access the dashboard**
   Open http://localhost:8080 in your browser

---

## Manual Testing

### 1. Test the API Directly

**Health Check**
```bash
curl http://localhost:5000/health
```

**Seed Database**
```bash
curl -X POST http://localhost:5000/api/seed
```

**Get Factory Metrics**
```bash
curl http://localhost:5000/api/metrics/factory
```

**Get All Workers**
```bash
curl http://localhost:5000/api/workers
```

**Send an Event**
```bash
curl -X POST http://localhost:5000/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2026-01-15T10:15:00Z",
    "worker_id": "W1",
    "workstation_id": "S1",
    "event_type": "working",
    "confidence": 0.95,
    "count": 0
  }'
```

### 2. Use the Test Script

```bash
# Install requests library if not already installed
pip install requests

# Run the test suite
python test_api.py
```

---

## Troubleshooting

### Port Already in Use

If port 5000 or 8080 is already in use:

**For Backend (port 5000)**
```bash
# Find process using port 5000
lsof -i :5000  # On Mac/Linux
netstat -ano | findstr :5000  # On Windows

# Kill the process or specify a different port in app.py
```

**For Frontend (port 8080)**
```bash
# Use a different port
python -m http.server 8081
# Then access at http://localhost:8081
```

### Database Issues

**Reset the database**
```bash
# Delete the database file (if running locally)
rm backend/factory_dashboard.db

# Or use the API endpoint
curl -X POST http://localhost:5000/api/seed
```

### CORS Errors

If you see CORS errors in browser console:
- Ensure the frontend is accessing `http://localhost:5000` (not `localhost:5000` with HTTPS)
- Check that Flask-CORS is properly installed: `pip install flask-cors`

### Events Not Appearing

1. Check that events have valid timestamps (ISO 8601 format)
2. Ensure worker_id and station_id exist in the database
3. Check the Flask console for any error messages

---

## Production Considerations

### Before Deploying to Production

1. **Security**
   - Add authentication to API endpoints
   - Implement rate limiting
   - Use HTTPS/TLS for all communications
   - Validate and sanitize all inputs

2. **Database**
   - Migrate from SQLite to PostgreSQL
   - Set up automated backups
   - Implement database indexing strategy

3. **Monitoring**
   - Set up centralized logging
   - Add health checks and alerting
   - Monitor API response times
   - Track error rates

4. **Scalability**
   - Use load balancer (Nginx, HAProxy)
   - Implement caching (Redis)
   - Use message queue (RabbitMQ, Kafka) for events
   - Enable horizontal scaling

5. **Configuration**
   - Use environment variables for configuration
   - Implement feature flags
   - Manage secrets securely

### Environment Variables

Create a `.env` file:
```
FLASK_ENV=production
DATABASE_URL=postgresql://user:password@localhost/factory_db
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
```

### Docker Production Build

```bash
# Build with production settings
docker build -f Dockerfile.backend --build-arg ENV=production -t factory-dashboard:1.0 .

# Use a production-grade WSGI server (Gunicorn)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## Monitoring and Maintenance

### Log Files

Check logs from running containers:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Performance Metrics

Monitor container resource usage:
```bash
docker stats
```

### Regular Maintenance

- Clear old events (e.g., older than 90 days)
- Rebuild database indexes monthly
- Review and optimize slow queries
- Update dependencies regularly

---

## Support

For issues or questions:
1. Check the README.md for architectural details
2. Review the API documentation in README.md
3. Run the test suite to verify setup
4. Check Docker logs for errors

