#!/bin/bash

# Quick Start Script for Factory Productivity Dashboard on Mac/Linux

echo ""
echo "======================================================================"
echo "  Factory Productivity Dashboard - Quick Start"
echo "======================================================================"
echo ""

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "Docker is installed. Starting with Docker Compose..."
    echo ""
    docker-compose up --build
else
    echo "Docker not found. Starting local development setup..."
    echo ""
    echo "This script will start both backend and frontend."
    echo "Two terminal windows will open."
    echo ""
    read -p "Press Enter to continue..."
    
    # Create a new terminal window for backend
    echo "Starting backend on port 5000..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open -a Terminal "$(pwd)/start_backend.sh"
    else
        # Linux
        gnome-terminal -- bash -c "cd backend && pip install -r requirements.txt && python app.py; bash"
    fi
    
    # Wait a moment for backend to start
    sleep 3
    
    # Start frontend
    echo "Starting frontend on port 8080..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open -a Terminal "$(pwd)/start_frontend.sh"
    else
        # Linux
        gnome-terminal -- bash -c "cd frontend && python -m http.server 8080; bash"
    fi
    
    echo ""
    echo "======================================================================"
    echo "  Services Starting..."
    echo "======================================================================"
    echo ""
    echo "Frontend:  http://localhost:8080"
    echo "Backend:   http://localhost:5000"
    echo "API Docs:  See README.md"
    echo ""
    echo "Press Ctrl+C in each terminal to stop the services."
    echo ""
fi
