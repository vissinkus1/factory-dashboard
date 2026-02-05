# 🚀 Getting Started Guide

**Factory Productivity Dashboard** - Complete Implementation

---

## What You Have

A full-stack AI-powered worker productivity monitoring system with:

✅ **Backend API** - Flask server with 12 RESTful endpoints  
✅ **Frontend Dashboard** - Interactive HTML/JS interface  
✅ **SQLite Database** - Pre-populated with 2 days of dummy data  
✅ **Docker Support** - Easy containerized deployment  
✅ **Documentation** - Comprehensive guides and examples  
✅ **Test Suite** - API validation and testing  

---

## ⚡ Quick Start (5 Minutes)

### Method 1: Docker Compose (Easiest)

```bash
# Navigate to project
cd dashnoard

# Start everything
docker-compose up --build
```

Then open:
- **Dashboard**: http://localhost:8080
- **API**: http://localhost:5000

**That's it!** The dashboard will load with pre-populated data.

### Method 2: Manual Startup (Windows)

Double-click `start.bat` in the project folder. This will:
1. Check for Docker (use Docker Compose if available)
2. Otherwise, start backend and frontend in separate command windows

### Method 3: Manual Startup (Mac/Linux)

```bash
# Terminal 1 - Backend
cd backend
pip install -r requirements.txt
python app.py

# Terminal 2 - Frontend
cd frontend
python -m http.server 8080
```

---

## 📊 Using the Dashboard

### 1. **View Metrics**

When you open http://localhost:8080, you'll see:

- **Factory Summary** (top) - Overall productivity stats
- **Worker Table** - 6 workers with utilization metrics
- **Workstation Table** - 6 stations with throughput data

### 2. **Filter Data**

Use the dropdown selectors to:
- Filter by specific worker
- Filter by specific workstation
- Click "Refresh Data" to reload

### 3. **Initialize Sample Data**

Click **"Reset with Dummy Data"** to:
- Clear existing data
- Load 2 days of realistic factory events
- Refresh all metrics

### 4. **Monitor in Real-Time**

The dashboard updates as new events arrive. You can:
- Send events via the API
- Watch metrics update automatically
- Filter to specific workers/stations

---

## 🔌 Testing the API

### Option 1: Test Script

```bash
# Run comprehensive test suite
pip install requests
python test_api.py
```

Expected output: "All tests passed! System is ready to use."

### Option 2: Manual cURL Tests

```bash
# Check if server is running
curl http://localhost:5000/health

# Get factory metrics
curl http://localhost:5000/api/metrics/factory

# Get all workers
curl http://localhost:5000/api/workers

# Send a test event
curl -X POST http://localhost:5000/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2026-02-06T14:30:00Z",
    "worker_id": "W1",
    "workstation_id": "S1",
    "event_type": "working",
    "confidence": 0.95,
    "count": 0
  }'
```

### Option 3: REST Client Extension

Use the file `API_EXAMPLES.rest`:
- Open in VS Code with REST Client extension
- Click "Send Request" on any example
- See response immediately

---

## 📂 File Guide

| File | Purpose |
|------|---------|
| `README.md` | Complete architecture & technical documentation |
| `DEPLOYMENT.md` | Setup guide & troubleshooting |
| `PROJECT_SUMMARY.md` | This project overview |
| `API_EXAMPLES.rest` | Sample API requests |
| `test_api.py` | Automated test suite |
| `backend/app.py` | Flask API server |
| `backend/database.py` | Database operations |
| `frontend/index.html` | Dashboard UI |
| `docker-compose.yml` | Container orchestration |
| `start.bat` / `start.sh` | Quick start scripts |

---

## 🔑 Key Endpoints

### Dashboard & Health
```
GET  http://localhost:5000/health              → Service status
```

### Workers
```
GET  http://localhost:5000/api/workers         → List all workers
GET  http://localhost:5000/api/metrics/workers → All worker metrics
GET  http://localhost:5000/api/metrics/workers/W1  → Specific worker
```

### Workstations
```
GET  http://localhost:5000/api/workstations    → List all stations
GET  http://localhost:5000/api/metrics/workstations → All station metrics
GET  http://localhost:5000/api/metrics/workstations/S1 → Specific station
```

### Events & Metrics
```
POST http://localhost:5000/api/events          → Send single event
POST http://localhost:5000/api/events/batch    → Send multiple events
GET  http://localhost:5000/api/metrics/factory → Factory metrics
POST http://localhost:5000/api/seed            → Reset with dummy data
```

---

## 📊 Sample Event Format

```json
{
  "timestamp": "2026-02-06T14:30:00Z",
  "worker_id": "W1",
  "workstation_id": "S1",
  "event_type": "working",
  "confidence": 0.95,
  "count": 0
}
```

### Event Types
- `working` - Worker actively producing
- `idle` - Worker present but not producing
- `absent` - Worker not at station
- `product_count` - Units produced (count field required)

### Valid Worker IDs: W1-W6
### Valid Station IDs: S1-S6

---

## 🧪 Sample Data Included

Pre-loaded with:
- **2 days** of realistic factory activity
- **432+ events** across all workers and stations
- **Time range**: 8 AM - 5 PM shifts
- **Event mix**: 60% working, 20% idle, 20% product_count

---

## 📈 Metrics Explained

### Worker Level
- **Active Time**: Hours spent working
- **Idle Time**: Hours at station but not producing
- **Utilization %**: (Active Time) / (Active + Idle) × 100
- **Units Produced**: Total items made
- **Units/Hour**: Production rate

### Workstation Level
- **Occupancy Time**: Hours station was in use
- **Utilization %**: Percentage of working hours occupied
- **Units Produced**: Items made at this station
- **Throughput**: Units per occupied hour

### Factory Level
- **Productive Hours**: Total worker active time
- **Production Count**: Total units made factory-wide
- **Production Rate**: Units per productive hour
- **Avg Utilization %**: Average across all workers

---

## 🔧 Troubleshooting

### "Connection Refused" Error

**Problem**: Can't connect to http://localhost:5000

**Solution**:
```bash
# Ensure backend is running
python backend/app.py

# If port 5000 is in use, check what's using it:
# Windows: netstat -ano | findstr :5000
# Mac/Linux: lsof -i :5000
```

### Dashboard Shows "Loading..." Forever

**Problem**: Frontend can't connect to API

**Solution**:
1. Verify backend is running
2. Check browser console (F12) for CORS errors
3. Ensure API is at http://localhost:5000
4. Try refreshing the page

### Database Lock Errors

**Problem**: "database is locked" error

**Solution**:
```bash
# Restart the backend
# Stop current process and run again
python backend/app.py
```

### Port Already in Use

**Problem**: "Address already in use"

**Solution**:
```bash
# For Python server (port 8080)
python -m http.server 8081  # Use different port

# For Flask (port 5000)
# Edit backend/app.py and change port:
# app.run(host='0.0.0.0', port=5001)
```

---

## 📚 Documentation Map

1. **Start Here**: `README.md` → Architecture & API docs
2. **For Setup**: `DEPLOYMENT.md` → Installation & troubleshooting
3. **See Examples**: `API_EXAMPLES.rest` → Sample requests
4. **Run Tests**: `test_api.py` → Validate setup
5. **Quick Ref**: This file → Getting started

---

## 🎯 Next Steps

### 1. **Explore the Dashboard**
- View factory metrics
- Filter by worker or workstation
- Click refresh to reload data

### 2. **Test the API**
- Run `python test_api.py`
- Try cURL commands from `API_EXAMPLES.rest`
- Send your own events

### 3. **Examine the Code**
- Backend logic in `backend/database.py`
- API endpoints in `backend/app.py`
- Dashboard UI in `frontend/index.html`

### 4. **Understand the Architecture**
- Read `README.md` for full technical details
- Learn how metrics are calculated
- Explore edge case handling

### 5. **Plan Extensions**
- Add authentication
- Switch to PostgreSQL
- Implement real-time updates (WebSocket)
- Add ML model integration

---

## 💡 Pro Tips

### Bulk Data Import
```bash
# Import multiple events at once
curl -X POST http://localhost:5000/api/events/batch \
  -H "Content-Type: application/json" \
  -d '[
    {"timestamp":"2026-02-06T14:30:00Z","worker_id":"W1","workstation_id":"S1","event_type":"working","confidence":0.95,"count":0},
    {"timestamp":"2026-02-06T14:45:00Z","worker_id":"W1","workstation_id":"S1","event_type":"idle","confidence":0.88,"count":0},
    {"timestamp":"2026-02-06T15:00:00Z","worker_id":"W1","workstation_id":"S1","event_type":"product_count","confidence":0.92,"count":5}
  ]'
```

### Export Metrics
All metrics endpoints return JSON. Save to file:
```bash
curl http://localhost:5000/api/metrics/factory > metrics.json
```

### Reset Everything
Click "Reset with Dummy Data" in dashboard, or:
```bash
curl -X POST http://localhost:5000/api/seed
```

### Monitor in Real-Time
Keep dashboard open in one window, send events in another:
```bash
# Watch metrics update as you send events
while true; do
  curl -X POST http://localhost:5000/api/events \
    -H "Content-Type: application/json" \
    -d '{"timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","worker_id":"W1","workstation_id":"S1","event_type":"working","confidence":0.95,"count":0}'
  sleep 5
done
```

---

## 🎓 Learning Resources

### Understand Each Component

**Database**:
- See `database/schema.sql` for table definitions
- Read metric calculation logic in `backend/database.py`

**API**:
- Review `backend/app.py` for all endpoints
- Check `API_EXAMPLES.rest` for request formats

**Frontend**:
- View `frontend/index.html` for UI code
- See JavaScript fetch calls for API integration

**Docker**:
- Check `docker-compose.yml` for service configuration
- Review `Dockerfile.backend` and `Dockerfile.frontend`

---

## 📞 Support

### If Something Doesn't Work

1. **Check the logs**:
   - Backend: See Flask console output
   - Frontend: Open browser DevTools (F12)

2. **Read the docs**:
   - `DEPLOYMENT.md` has extensive troubleshooting
   - `README.md` explains architecture and edge cases

3. **Verify setup**:
   - Run `python test_api.py` to validate everything
   - Check that ports 5000 and 8080 are free

4. **Check requirements**:
   - Python 3.10+ installed?
   - Flask and Flask-CORS installed?
   - Docker installed (if using Docker)?

---

## ✨ You're All Set!

Everything is ready to go. Just run one of these commands and you're in business:

```bash
# Docker (recommended)
docker-compose up --build

# Or local
python backend/app.py    # Terminal 1
python -m http.server 8080  # Terminal 2
```

Then visit **http://localhost:8080** and explore!

---

**Questions?** Check the README.md or DEPLOYMENT.md for detailed documentation.

**Happy monitoring!** 🎉
