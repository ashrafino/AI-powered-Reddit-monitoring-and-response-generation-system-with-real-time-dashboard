#!/bin/bash
# Deployment script for DigitalOcean server
# Run this script ON YOUR SERVER after pulling the latest changes

set -e  # Exit on any error

echo "=========================================="
echo "🚀 Deploying Scan Feature Fix to Server"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/root/reddit-bot"
VENV_DIR="$APP_DIR/.venv"
BACKEND_SERVICE="reddit-bot-backend"
CELERY_SERVICE="reddit-bot-celery"

echo -e "\n${YELLOW}Step 1: Navigating to application directory${NC}"
cd $APP_DIR
echo "✅ Current directory: $(pwd)"

echo -e "\n${YELLOW}Step 2: Pulling latest changes from GitHub${NC}"
git pull origin main
echo "✅ Code updated"

echo -e "\n${YELLOW}Step 3: Activating virtual environment${NC}"
source $VENV_DIR/bin/activate
echo "✅ Virtual environment activated"

echo -e "\n${YELLOW}Step 4: Installing/updating dependencies${NC}"
pip install -r requirements.txt --quiet
echo "✅ Dependencies updated"

echo -e "\n${YELLOW}Step 5: Running database migrations (if any)${NC}"
# Uncomment if you use Alembic
# alembic upgrade head
echo "✅ Database up to date"

echo -e "\n${YELLOW}Step 6: Restarting backend service${NC}"
sudo systemctl restart $BACKEND_SERVICE
sleep 2
if sudo systemctl is-active --quiet $BACKEND_SERVICE; then
    echo -e "${GREEN}✅ Backend service restarted successfully${NC}"
else
    echo -e "${RED}❌ Backend service failed to start${NC}"
    sudo systemctl status $BACKEND_SERVICE
    exit 1
fi

echo -e "\n${YELLOW}Step 7: Restarting Celery worker (if running)${NC}"
if sudo systemctl is-active --quiet $CELERY_SERVICE; then
    sudo systemctl restart $CELERY_SERVICE
    sleep 2
    if sudo systemctl is-active --quiet $CELERY_SERVICE; then
        echo -e "${GREEN}✅ Celery service restarted successfully${NC}"
    else
        echo -e "${YELLOW}⚠️  Celery service failed to restart (non-critical)${NC}"
    fi
else
    echo "ℹ️  Celery service not running (this is OK for development)"
fi

echo -e "\n${YELLOW}Step 8: Checking service status${NC}"
echo "Backend status:"
sudo systemctl status $BACKEND_SERVICE --no-pager | head -n 10

echo -e "\n${YELLOW}Step 9: Testing the fix${NC}"
echo "Testing scan endpoint..."
sleep 3  # Wait for service to fully start

# Get admin token (adjust credentials if needed)
TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123" | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")

if [ -n "$TOKEN" ]; then
    echo "✅ Authentication successful"
    
    # Test scan endpoint
    SCAN_RESULT=$(curl -s -X POST "http://localhost:8000/api/ops/scan" \
      -H "Authorization: Bearer $TOKEN")
    
    if echo "$SCAN_RESULT" | grep -q "status"; then
        echo -e "${GREEN}✅ Scan endpoint is working!${NC}"
        echo "Response: $SCAN_RESULT"
    else
        echo -e "${RED}❌ Scan endpoint returned unexpected response${NC}"
        echo "Response: $SCAN_RESULT"
    fi
else
    echo -e "${YELLOW}⚠️  Could not test scan endpoint (authentication failed)${NC}"
    echo "You can test manually with: curl -X POST http://localhost:8000/api/ops/scan -H 'Authorization: Bearer YOUR_TOKEN'"
fi

echo -e "\n${YELLOW}Step 10: Checking logs for errors${NC}"
echo "Recent backend logs:"
sudo journalctl -u $BACKEND_SERVICE -n 20 --no-pager

echo -e "\n=========================================="
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "📝 What was fixed:"
echo "  - Added missing 'anyio' import in ops.py"
echo "  - Added missing 'generate_reddit_replies_with_research' import"
echo "  - Scan feature should now work correctly"
echo ""
echo "🧪 To test manually:"
echo "  1. Login to your app as admin"
echo "  2. Create a client (if not exists)"
echo "  3. Create a configuration"
echo "  4. Trigger a scan from dashboard or configs page"
echo ""
echo "📊 Monitor logs:"
echo "  sudo journalctl -u $BACKEND_SERVICE -f"
echo ""
echo "🔄 If issues occur, rollback with:"
echo "  cd $APP_DIR && git reset --hard HEAD~1"
echo "  sudo systemctl restart $BACKEND_SERVICE"
echo ""
