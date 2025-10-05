#!/bin/bash
# Quick script to start backend locally

source .venv/bin/activate

# Initialize database
echo "Initializing database..."
python -m app.scripts.db

# Create admin user
echo "Creating admin user..."
python -m app.scripts.create_admin

# Start the server
echo "Starting backend server on http://localhost:8001"
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
