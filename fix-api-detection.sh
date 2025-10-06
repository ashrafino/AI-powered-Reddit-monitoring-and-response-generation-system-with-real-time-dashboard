#!/bin/bash

# Fix API Detection - Rebuild Frontend with Runtime Detection
# This script rebuilds the frontend to use runtime API detection
# No more hardcoded IPs!

set -e

echo "🔧 Fixing API Detection Issue..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on server or local
if [ -d "/home/deploy/apps/reddit-bot" ]; then
    APP_DIR="/home/deploy/apps/reddit-bot"
    echo -e "${BLUE}📍 Detected production server${NC}"
else
    APP_DIR="."
    echo -e "${BLUE}📍 Running locally${NC}"
fi

cd "$APP_DIR"

echo ""
echo -e "${YELLOW}Step 1: Stopping frontend container...${NC}"
sudo docker-compose -f docker-compose.prod.yml stop frontend

echo ""
echo -e "${YELLOW}Step 2: Rebuilding frontend with runtime detection...${NC}"
sudo docker-compose -f docker-compose.prod.yml build frontend --no-cache

echo ""
echo -e "${YELLOW}Step 3: Starting frontend...${NC}"
sudo docker-compose -f docker-compose.prod.yml up -d frontend

echo ""
echo -e "${GREEN}✅ Frontend rebuilt successfully!${NC}"
echo ""
echo "The frontend now uses runtime API detection:"
echo "  • Development: http://localhost:8001"
echo "  • Production: Relative URLs (nginx proxy)"
echo ""
echo "Check browser console for detection logs:"
echo "  sudo docker-compose -f docker-compose.prod.yml logs -f frontend"
echo ""
echo -e "${GREEN}🎉 No more hardcoded IPs!${NC}"
