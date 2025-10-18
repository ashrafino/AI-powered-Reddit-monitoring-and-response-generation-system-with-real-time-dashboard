# Server Deployment Commands

## Quick Deployment (Recommended)

### Step 1: SSH into your server
```bash
ssh root@your-server-ip
```

### Step 2: Navigate to app directory
```bash
cd /root/reddit-bot
```

### Step 3: Pull latest changes
```bash
git pull origin main
```

### Step 4: Run deployment script
```bash
# If you copied the script to server
bash DEPLOY_TO_SERVER.sh

# OR follow manual steps below
```

---

## Manual Deployment Steps

### 1. SSH into Server
```bash
ssh root@your-server-ip
# Or if using a different user:
# ssh username@your-server-ip
```

### 2. Navigate to Application Directory
```bash
cd /root/reddit-bot
# Verify you're in the right place
pwd
ls -la
```

### 3. Pull Latest Changes
```bash
git pull origin main
```

Expected output:
```
remote: Enumerating objects: 15, done.
remote: Counting objects: 100% (15/15), done.
...
Updating 5bab9f8..1e052b0
Fast-forward
 app/api/routers/ops.py | 4 +++-
 ...
```

### 4. Activate Virtual Environment
```bash
source .venv/bin/activate
```

### 5. Update Dependencies (if needed)
```bash
pip install -r requirements.txt
```

### 6. Restart Backend Service
```bash
sudo systemctl restart reddit-bot-backend

# Check status
sudo systemctl status reddit-bot-backend
```

Expected output:
```
● reddit-bot-backend.service - Reddit Bot Backend
   Loaded: loaded
   Active: active (running)
```

### 7. Restart Celery Worker (if running)
```bash
# Check if Celery is running
sudo systemctl status reddit-bot-celery

# If running, restart it
sudo systemctl restart reddit-bot-celery
```

### 8. Verify Services are Running
```bash
# Check backend
sudo systemctl is-active reddit-bot-backend

# Check Celery (optional)
sudo systemctl is-active reddit-bot-celery

# View recent logs
sudo journalctl -u reddit-bot-backend -n 50 --no-pager
```

### 9. Test the Fix
```bash
# Test health endpoint
curl http://localhost:8000/api/health

# Login and get token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123" | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "Token: $TOKEN"

# Test scan endpoint
curl -X POST "http://localhost:8000/api/ops/scan" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

Expected response:
```json
{
  "status": "completed",
  "method": "sync",
  "created_posts": 0,
  "created_responses": 0
}
```

---

## Troubleshooting

### If Backend Won't Start

```bash
# Check logs for errors
sudo journalctl -u reddit-bot-backend -n 100 --no-pager

# Check if port is in use
sudo lsof -i :8000

# Try manual start to see errors
cd /root/reddit-bot
source .venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### If Import Errors Occur

```bash
# Verify the fix was applied
cd /root/reddit-bot
grep -n "import anyio" app/api/routers/ops.py
grep -n "generate_reddit_replies_with_research" app/api/routers/ops.py

# Should see:
# Line 6: import anyio
# Line 17: ...generate_reddit_replies_with_research
```

### If Scan Still Fails

```bash
# Check Reddit API credentials
cd /root/reddit-bot
source .venv/bin/activate
python3 << EOF
from app.services.reddit_service import test_reddit_connection
print(test_reddit_connection())
EOF

# Check OpenAI API key
python3 << EOF
from app.core.config import settings
print("OpenAI configured:", bool(settings.openai_api_key))
EOF
```

### View Live Logs

```bash
# Follow backend logs in real-time
sudo journalctl -u reddit-bot-backend -f

# In another terminal, trigger a scan and watch logs
```

---

## Rollback (If Needed)

If something goes wrong:

```bash
cd /root/reddit-bot

# Rollback to previous commit
git reset --hard HEAD~1

# Restart services
sudo systemctl restart reddit-bot-backend
sudo systemctl restart reddit-bot-celery

# Verify
sudo systemctl status reddit-bot-backend
```

---

## Post-Deployment Verification

### 1. Check via Browser
- Go to your domain: `https://your-domain.com`
- Login as admin
- Navigate to Configs page
- Create a test configuration with "Auto-scan" enabled
- Verify scan completes successfully

### 2. Check Database
```bash
# Connect to database
psql -U redditbot_user -d redditbot

# Check for new posts
SELECT COUNT(*) FROM matched_posts;

# Check for new responses
SELECT COUNT(*) FROM ai_responses;

# Exit
\q
```

### 3. Monitor for Errors
```bash
# Watch logs for 5 minutes
sudo journalctl -u reddit-bot-backend -f

# Look for:
# ✅ No import errors
# ✅ Scan completes successfully
# ✅ Posts and responses created
```

---

## Service Management Commands

```bash
# Start service
sudo systemctl start reddit-bot-backend

# Stop service
sudo systemctl stop reddit-bot-backend

# Restart service
sudo systemctl restart reddit-bot-backend

# Check status
sudo systemctl status reddit-bot-backend

# Enable on boot
sudo systemctl enable reddit-bot-backend

# View logs
sudo journalctl -u reddit-bot-backend -n 100

# Follow logs
sudo journalctl -u reddit-bot-backend -f
```

---

## Environment Variables Check

```bash
cd /root/reddit-bot

# Check if .env.production exists
ls -la .env.production

# Verify critical variables (without showing values)
grep -E "REDDIT_|OPENAI_|DATABASE_" .env.production | sed 's/=.*/=***/'
```

---

## Success Criteria

After deployment, verify:

- ✅ Backend service is running
- ✅ No import errors in logs
- ✅ Health endpoint responds: `curl http://localhost:8000/api/health`
- ✅ Can login via frontend
- ✅ Can create clients (admin only)
- ✅ Can create configurations
- ✅ Can trigger scans
- ✅ Scans complete successfully
- ✅ Posts are created
- ✅ AI responses are generated

---

## Quick Reference

```bash
# One-liner deployment
ssh root@your-server-ip "cd /root/reddit-bot && git pull && source .venv/bin/activate && pip install -r requirements.txt && sudo systemctl restart reddit-bot-backend && sudo systemctl status reddit-bot-backend"

# Check if fix is applied
ssh root@your-server-ip "grep -n 'import anyio' /root/reddit-bot/app/api/routers/ops.py"

# View recent logs
ssh root@your-server-ip "sudo journalctl -u reddit-bot-backend -n 50 --no-pager"
```

---

## Support

If you encounter issues:

1. Check the logs: `sudo journalctl -u reddit-bot-backend -n 100`
2. Verify the fix: `grep "import anyio" app/api/routers/ops.py`
3. Test manually: Try the scan endpoint via curl
4. Rollback if needed: `git reset --hard HEAD~1`

The fix is minimal and safe - it only adds missing imports. No database changes, no configuration changes.
