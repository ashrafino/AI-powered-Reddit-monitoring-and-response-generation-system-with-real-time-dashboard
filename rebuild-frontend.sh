#!/bin/bash
set -e

echo "🔄 Rebuilding frontend with dynamic API detection..."

# Stop frontend
docker-compose -f docker-compose.prod.yml stop frontend

# Remove old frontend container and image
docker-compose -f docker-compose.prod.yml rm -f frontend
docker rmi $(docker images -q reddit-bot-frontend) 2>/dev/null || true

# Rebuild frontend (no cache to ensure fresh build)
docker-compose -f docker-compose.prod.yml build --no-cache frontend

# Start frontend
docker-compose -f docker-compose.prod.yml up -d frontend

echo "✅ Frontend rebuilt successfully!"
echo ""
echo "📊 Checking status..."
sleep 5
docker-compose -f docker-compose.prod.yml ps frontend
echo ""
echo "📝 Recent logs:"
docker-compose -f docker-compose.prod.yml logs --tail=20 frontend
