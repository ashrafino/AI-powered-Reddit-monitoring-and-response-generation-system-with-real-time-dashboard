#!/bin/bash

# Quick fix for 400 error - most likely causes

set -e

echo "🔍 Diagnosing 400 Bad Request Error..."
echo ""

# Check if we're on the server
if [ ! -d "/home/deploy/apps/reddit-bot" ]; then
    echo "❌ This script must be run on the production server"
    echo "Run: ssh root@146.190.50.85"
    exit 1
fi

cd /home/deploy/apps/reddit-bot

echo "1️⃣ Checking if admin user exists..."
sudo docker-compose -f docker-compose.prod.yml exec -T backend python -c "
from app.db.session import SessionLocal
from app.models.user import User
db = SessionLocal()
admin = db.query(User).filter(User.email == 'admin@example.com').first()
if admin:
    print('✅ Admin user exists')
else:
    print('❌ Admin user NOT found - creating now...')
    exit(1)
db.close()
" || {
    echo "Creating admin user..."
    sudo docker-compose -f docker-compose.prod.yml exec -T backend python -m app.scripts.create_admin
}

echo ""
echo "2️⃣ Testing backend directly..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Backend login works directly"
else
    echo "❌ Backend login failed with status: $HTTP_CODE"
    echo "Response: $BODY"
fi

echo ""
echo "3️⃣ Testing through nginx..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Nginx proxy works correctly"
else
    echo "❌ Nginx proxy failed with status: $HTTP_CODE"
    echo "Response: $BODY"
    echo ""
    echo "Checking nginx logs..."
    sudo docker-compose -f docker-compose.prod.yml logs --tail=10 nginx
fi

echo ""
echo "4️⃣ Checking recent backend logs..."
sudo docker-compose -f docker-compose.prod.yml logs --tail=20 backend | grep -i "error\|400\|login" || echo "No errors found in recent logs"

echo ""
echo "✅ Diagnosis complete!"
echo ""
echo "Next steps:"
echo "1. Check browser Network tab for the actual error response"
echo "2. Try the manual test from browser console (see DEBUG_400_ERROR.md)"
echo "3. If still failing, run: sudo docker-compose -f docker-compose.prod.yml logs -f backend"
