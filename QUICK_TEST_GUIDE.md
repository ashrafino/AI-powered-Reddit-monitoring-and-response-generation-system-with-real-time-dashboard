# Quick Test Guide - Client Creation & Scan Feature

## Prerequisites Check

```bash
# 1. Check if PostgreSQL is running
psql -U macbook -d redditbot -c "SELECT 1;"

# 2. Check if Redis is running (optional, for Celery)
redis-cli ping

# 3. Verify environment variables
cat .env | grep -E "REDDIT_|OPENAI_|DATABASE_"
```

## Start the Backend

```bash
# Option 1: Using the start script
./START_BACKEND.sh

# Option 2: Manual start
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Run Tests

### Automated Test
```bash
python test_client_and_scan.py
```

Expected output:
```
============================================================
Testing Client Creation and Scan Functionality
============================================================

🔐 Testing login...
✅ Login successful

📋 Listing clients...
✅ Found X clients

➕ Creating test client...
✅ Client created: Test Client 1234567890 (ID: X)

⚙️  Creating config for client X...
✅ Config created (ID: X)

📋 Listing configs...
✅ Found X configs

🔄 Triggering scan...
✅ Scan triggered successfully
   Status: completed
   Method: sync
   Posts created: X
   Responses created: X

📋 Listing posts...
✅ Found X posts

============================================================
✅ All tests completed!
============================================================
```

## Manual Testing via Browser

### 1. Access Frontend
```bash
cd frontend
npm run dev
```

Open: http://localhost:3000

### 2. Login
- Email: `admin@example.com`
- Password: `admin123`

### 3. Create Client
1. Click "Clients" in navigation
2. Enter client name: "My Test Company"
3. Click "Create Client"
4. ✅ Should see success message

### 4. Create Configuration
1. Click "Configs" in navigation
2. Select the client you created
3. Enter subreddits: `technology, programming, webdev`
4. Enter keywords: `API, integration, automation`
5. Check "Auto-scan after creating"
6. Click "Create Configuration"
7. ✅ Should see success message and scan should start

### 5. View Results
1. Click "Dashboard"
2. ✅ Should see matched posts
3. Click on a post to see AI-generated responses

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.10+

# Install dependencies
pip install -r requirements.txt

# Check database connection
psql -U macbook -d redditbot -c "SELECT COUNT(*) FROM users;"
```

### No clients showing up
- Make sure you're logged in as admin
- Check browser console for errors
- Verify backend is running: `curl http://localhost:8000/api/health`

### Scan not working
```bash
# Check Reddit API credentials
python -c "from app.services.reddit_service import test_reddit_connection; print(test_reddit_connection())"

# Check OpenAI API key
python -c "from app.core.config import settings; print('OpenAI configured:', bool(settings.openai_api_key))"
```

### No posts found
- This is normal if keywords don't match recent posts
- Try broader keywords: `python, javascript, help`
- Try popular subreddits: `learnprogramming, webdev`

## API Endpoints Reference

### Authentication
```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123"
```

### Clients
```bash
# List clients (admin only)
curl http://localhost:8000/api/clients \
  -H "Authorization: Bearer YOUR_TOKEN"

# Create client (admin only)
curl -X POST http://localhost:8000/api/clients \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Client"}'
```

### Configs
```bash
# List configs
curl http://localhost:8000/api/configs \
  -H "Authorization: Bearer YOUR_TOKEN"

# Create config
curl -X POST http://localhost:8000/api/configs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1,
    "reddit_subreddits": ["technology"],
    "keywords": ["API"],
    "is_active": true,
    "scan_interval_minutes": 360,
    "scan_start_hour": 0,
    "scan_end_hour": 23,
    "scan_days": "1,2,3,4,5,6,7"
  }'
```

### Scan
```bash
# Trigger manual scan
curl -X POST http://localhost:8000/api/ops/scan \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Posts
```bash
# List posts
curl http://localhost:8000/api/posts \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Success Criteria

✅ Backend starts without errors
✅ Can login as admin
✅ Can create a client
✅ Can create a configuration
✅ Can trigger a scan
✅ Scan completes successfully
✅ Posts are created in database
✅ AI responses are generated
✅ Dashboard shows results

## Next Steps

After verifying everything works:

1. **Create real clients** for your use case
2. **Configure meaningful keywords** for your industry
3. **Set up scheduled scans** using Celery Beat
4. **Monitor scan results** on the dashboard
5. **Fine-tune keywords** based on results

## Support

If you encounter issues:
1. Check the backend logs
2. Check browser console
3. Verify all environment variables are set
4. Ensure database is accessible
5. Confirm Reddit/OpenAI API keys are valid
