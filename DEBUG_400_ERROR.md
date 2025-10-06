# Debugging 400 Bad Request Error

## Current Status
✅ API detection working - using relative URLs correctly
❌ Getting 400 Bad Request on login

## Quick Diagnosis Commands

Run these on your server to diagnose the issue:

```bash
# SSH into server
ssh root@146.190.50.85
cd /home/deploy/apps/reddit-bot

# 1. Check if admin user exists
sudo docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.db.session import SessionLocal
from app.models.user import User
db = SessionLocal()
admin = db.query(User).filter(User.email == 'admin@example.com').first()
if admin:
    print(f'✅ Admin user exists: {admin.email}')
    print(f'   Active: {admin.is_active}')
    print(f'   Client ID: {admin.client_id}')
else:
    print('❌ Admin user NOT found')
db.close()
"

# 2. Test login directly to backend (bypassing nginx)
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123" \
  -w "\nHTTP Status: %{http_code}\n"

# 3. Test login through nginx (what frontend uses)
curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123" \
  -w "\nHTTP Status: %{http_code}\n"

# 4. Check backend logs for the actual error
sudo docker-compose -f docker-compose.prod.yml logs --tail=50 backend | grep -A 5 -B 5 "400\|ERROR\|login"

# 5. Check nginx logs
sudo docker-compose -f docker-compose.prod.yml logs --tail=30 nginx
```

## Common Causes of 400 Error

### 1. Admin User Not Created
**Symptom:** Backend returns "Email and password are required"
**Fix:**
```bash
sudo docker-compose -f docker-compose.prod.yml exec backend python -m app.scripts.create_admin
```

### 2. Wrong Password
**Symptom:** Backend returns "Incorrect email or password"
**Fix:** Check .env file for correct ADMIN_PASSWORD

### 3. Request Body Not Being Sent
**Symptom:** Backend receives empty form data
**Fix:** Check nginx is not stripping the body

### 4. Content-Type Header Issue
**Symptom:** Backend can't parse form data
**Fix:** Ensure Content-Type is application/x-www-form-urlencoded

## Expected Successful Response

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

## If Still Failing

### Enable Debug Logging

1. Edit docker-compose.prod.yml:
```yaml
backend:
  environment:
    - LOG_LEVEL=DEBUG
```

2. Restart backend:
```bash
sudo docker-compose -f docker-compose.prod.yml restart backend
```

3. Watch logs in real-time:
```bash
sudo docker-compose -f docker-compose.prod.yml logs -f backend
```

4. Try login from browser and watch the logs

### Check Network Request in Browser

1. Open browser DevTools (F12)
2. Go to Network tab
3. Try to login
4. Click on the `/api/auth/login` request
5. Check:
   - Request Headers (should have Content-Type: application/x-www-form-urlencoded)
   - Request Payload (should have username and password)
   - Response (should show the actual error message)

### Manual Test from Browser Console

```javascript
// Run this in browser console at http://146.190.50.85
fetch('/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  body: new URLSearchParams({
    username: 'admin@example.com',
    password: 'admin123'
  }).toString()
})
.then(r => r.json())
.then(console.log)
.catch(console.error)
```

## Next Steps

1. Run the diagnosis commands above
2. Share the output of the backend logs
3. Check the Network tab in browser DevTools for the actual error response body
