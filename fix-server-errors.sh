#!/bin/bash

# Comprehensive server error fix script
# Run this on the server to diagnose and fix common issues

set -e

echo "🔍 Reddit Bot - Error Diagnosis and Fix Script"
echo "=============================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_DIR="/home/deploy/apps/reddit-bot"

cd "$PROJECT_DIR"

echo "📍 Current directory: $(pwd)"
echo ""

# Function to check service health
check_service() {
    local service=$1
    local status=$(docker-compose ps -q $service 2>/dev/null)
    
    if [ -z "$status" ]; then
        echo -e "${RED}❌ $service: Not running${NC}"
        return 1
    else
        local health=$(docker inspect --format='{{.State.Health.Status}}' $(docker-compose ps -q $service) 2>/dev/null || echo "unknown")
        if [ "$health" = "healthy" ] || [ "$health" = "unknown" ]; then
            echo -e "${GREEN}✅ $service: Running${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  $service: Running but unhealthy${NC}"
            return 1
        fi
    fi
}

# Check all services
echo "🔍 Checking Services..."
echo "----------------------"
check_service postgres
check_service redis
check_service backend
check_service frontend
check_service worker
check_service beat
check_service nginx
echo ""

# Check for common errors in logs
echo "🔍 Checking for Common Errors..."
echo "--------------------------------"

# Check backend logs for errors
echo "Backend errors:"
docker-compose logs backend --tail=50 2>/dev/null | grep -i "error\|fatal\|exception" | tail -5 || echo "  No recent errors"
echo ""

# Check worker logs
echo "Worker errors:"
docker-compose logs worker --tail=50 2>/dev/null | grep -i "error\|fatal\|exception" | tail -5 || echo "  No recent errors"
echo ""

# Check database connection
echo "🔍 Checking Database Connection..."
echo "-----------------------------------"
if docker-compose exec -T postgres psql -U postgres -d redditbot -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Database connection: OK${NC}"
else
    echo -e "${RED}❌ Database connection: FAILED${NC}"
    echo "Attempting to fix..."
    docker-compose restart postgres
    sleep 5
fi
echo ""

# Check if default client exists
echo "🔍 Checking Default Client..."
echo "-----------------------------"
CLIENT_COUNT=$(docker-compose exec -T backend python -c "
from app.db.session import SessionLocal
from app.models.client import Client
db = SessionLocal()
count = db.query(Client).count()
print(count)
db.close()
" 2>/dev/null || echo "0")

if [ "$CLIENT_COUNT" -eq "0" ]; then
    echo -e "${YELLOW}⚠️  No clients found. Creating default client...${NC}"
    docker-compose exec -T backend python -m app.scripts.create_default_client
    echo -e "${GREEN}✅ Default client created${NC}"
else
    echo -e "${GREEN}✅ Found $CLIENT_COUNT client(s)${NC}"
fi
echo ""

# Check if admin user exists
echo "🔍 Checking Admin User..."
echo "-------------------------"
ADMIN_EXISTS=$(docker-compose exec -T backend python -c "
from app.db.session import SessionLocal
from app.models.user import User
db = SessionLocal()
admin = db.query(User).filter(User.email == 'admin@example.com').first()
print('yes' if admin else 'no')
db.close()
" 2>/dev/null || echo "no")

if [ "$ADMIN_EXISTS" = "no" ]; then
    echo -e "${YELLOW}⚠️  Admin user not found. Creating...${NC}"
    docker-compose exec -T backend python -m app.scripts.create_admin
    echo -e "${GREEN}✅ Admin user created${NC}"
else
    echo -e "${GREEN}✅ Admin user exists${NC}"
fi
echo ""

# Check API endpoints
echo "🔍 Checking API Endpoints..."
echo "----------------------------"

# Health check
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ /api/health: OK${NC}"
else
    echo -e "${RED}❌ /api/health: FAILED${NC}"
fi

# Clients endpoint
if curl -s -H "Authorization: Bearer test" http://localhost:8000/api/clients > /dev/null 2>&1; then
    echo -e "${GREEN}✅ /api/clients: OK${NC}"
else
    echo -e "${YELLOW}⚠️  /api/clients: May require authentication${NC}"
fi
echo ""

# Check Celery
echo "🔍 Checking Celery..."
echo "--------------------"
if docker-compose ps | grep -q "worker.*Up"; then
    echo -e "${GREEN}✅ Celery worker: Running${NC}"
else
    echo -e "${RED}❌ Celery worker: Not running${NC}"
    echo "Restarting worker..."
    docker-compose restart worker
fi

if docker-compose ps | grep -q "beat.*Up"; then
    echo -e "${GREEN}✅ Celery beat: Running${NC}"
else
    echo -e "${RED}❌ Celery beat: Not running${NC}"
    echo "Restarting beat..."
    docker-compose restart beat
fi
echo ""

# Check disk space
echo "🔍 Checking Disk Space..."
echo "-------------------------"
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo -e "${RED}❌ Disk usage: ${DISK_USAGE}% (Critical)${NC}"
    echo "Consider cleaning up Docker images:"
    echo "  docker system prune -a"
else
    echo -e "${GREEN}✅ Disk usage: ${DISK_USAGE}%${NC}"
fi
echo ""

# Check memory
echo "🔍 Checking Memory..."
echo "--------------------"
FREE_MEM=$(free -m | awk 'NR==2 {print $7}')
if [ "$FREE_MEM" -lt 200 ]; then
    echo -e "${YELLOW}⚠️  Low memory: ${FREE_MEM}MB available${NC}"
else
    echo -e "${GREEN}✅ Memory: ${FREE_MEM}MB available${NC}"
fi
echo ""

# Summary
echo "📊 Summary"
echo "=========="
echo "Run these commands for more details:"
echo "  docker-compose logs backend --tail=50"
echo "  docker-compose logs worker --tail=50"
echo "  docker-compose logs -f  # Follow all logs"
echo ""
echo "To restart all services:"
echo "  docker-compose restart"
echo ""
echo "To rebuild and restart:"
echo "  docker-compose down && docker-compose up -d --build"
echo ""
