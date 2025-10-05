#!/bin/bash
# Stop any Docker backend containers first
docker stop redditbot-backend-dev-1 2>/dev/null
docker rm redditbot-backend-dev-1 2>/dev/null

# Wait a moment
sleep 2

# Start the backend locally
cd "/Users/macbook/Documents/REDDIT BOT"
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
