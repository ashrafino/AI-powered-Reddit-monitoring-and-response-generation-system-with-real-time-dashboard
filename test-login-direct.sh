#!/bin/bash

# Test login directly on the server to see the exact error

echo "Testing backend login endpoint..."
echo ""

# Test 1: Direct backend call
echo "1. Testing direct backend (should work):"
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123" \
  -v

echo ""
echo ""

# Test 2: Through nginx
echo "2. Testing through nginx (what frontend uses):"
curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123" \
  -v

echo ""
echo ""

# Test 3: Check nginx logs
echo "3. Checking nginx error logs:"
docker-compose -f docker-compose.prod.yml logs --tail=20 nginx

echo ""
echo ""

# Test 4: Check backend logs
echo "4. Checking backend logs:"
docker-compose -f docker-compose.prod.yml logs --tail=20 backend
