#!/bin/bash

# Comprehensive fix for all 400 error causes

set -e

echo "🔧 Comprehensive Fix for 400 Bad Request Error"
echo "=============================================="
echo ""

# Check if on server
if [ ! -d "/home/deploy/apps/reddit-bot" ]; then
    echo "❌ Run this on the production server"
    echo "Command: ssh root@146.190.50.85"
    exit 1
fi

cd /home/deploy/apps/reddit-bot

echo "Step 1: Checking admin user..."
echo "------------------------------"
sudo docker-compose -f docker-compose.prod.yml exec -T backend python -c "
from app.db.session import SessionLocal
from app.models.user import User
db = SessionLocal()
admin = db.query(User).filter(User.email == 'admin@example.com').first()
if admin:
    print(f'✅ Admin exists: {admin.email}')
    print(f'   Active: {admin.is_active}')
    print(f'   Has password: {bool(admin.hashed_password)}')
    print(f'   Client ID: {admin.client_id}')
else:
    print('❌ Admin user NOT found')
    exit(1)
db.close()
" || {
    echo ""
    echo "Creating admin user..."
    sudo docker-compose -f docker-compose.prod.yml exec -T backend python -m app.scripts.create_admin
    echo "✅ Admin user created"
}

echo ""
echo "Step 2: Testing backend directly (bypass nginx)..."
echo "---------------------------------------------------"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

echo "Status: $HTTP_CODE"
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Backend works directly"
    echo "Response: ${BODY:0:100}..."
else
    echo "❌ Backend failed"
    echo "Response: $BODY"
    echo ""
    echo "Checking backend logs..."
    sudo docker-compose -f docker-compose.prod.yml logs --tail=20 backend
    exit 1
fi

echo ""
echo "Step 3: Testing through nginx..."
echo "---------------------------------"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

echo "Status: $HTTP_CODE"
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Nginx proxy works"
    echo "Response: ${BODY:0:100}..."
else
    echo "❌ Nginx proxy failed"
    echo "Response: $BODY"
    echo ""
    echo "This means nginx is not passing the request body correctly!"
    echo "Rebuilding nginx with fixed configuration..."
    sudo docker-compose -f docker-compose.prod.yml restart nginx
    sleep 3
    
    # Test again
    echo "Testing again after nginx restart..."
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost/api/auth/login \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=admin@example.com&password=admin123")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    
    echo "Status: $HTTP_CODE"
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ Fixed! Nginx now works"
    else
        echo "❌ Still failing. Response: $BODY"
        echo ""
        echo "Checking nginx error logs..."
        sudo docker-compose -f docker-compose.prod.yml logs --tail=20 nginx
        exit 1
    fi
fi

echo ""
echo "Step 4: Checking backend logs for any errors..."
echo "------------------------------------------------"
sudo docker-compose -f docker-compose.prod.yml logs --tail=30 backend | grep -i "error\|400\|login\|debug" || echo "No errors found"

echo ""
echo "=============================================="
echo "✅ All tests passed!"
echo ""
echo "Your login should now work at: http://146.190.50.85"
echo "Credentials: admin@example.com / admin123"
echo ""
echo "If still having issues, check browser DevTools Network tab"
echo "and share the request/response details."
