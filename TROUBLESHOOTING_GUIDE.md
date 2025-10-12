# Troubleshooting Guide

## 🐛 Common Issues and Solutions

### 1. "Unknown date" or "Invalid Date" ✅ FIXED

**Problem:** Dates showing as "Unknown date" or "Invalid Date"

**Root Cause:** The backend schema wasn't including `created_at` field in API responses

**Solution:** Updated `app/schemas/post.py` to include `created_at` for both posts and responses

**Deploy Fix:**
```bash
cd /home/deploy/apps/reddit-bot
git pull origin main
docker-compose -f docker-compose.prod.yml restart backend
docker-compose -f docker-compose.prod.yml restart frontend
```

**Verify Fix:**
- Dates should now show: "Dec 10, 2025 02:30 PM"
- Both post dates and response dates should display correctly

---

### 2. Clients Link Not Working

**Problem:** Can see "Clients" link but clicking doesn't navigate

**Possible Causes:**

#### A. Not an Admin User
**Check:** Only admin users can access the Clients page

**Solution:**
1. Verify your user role:
```bash
# On server
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.db.session import SessionLocal
from app.models.user import User
db = SessionLocal()
user = db.query(User).filter(User.email == 'YOUR_EMAIL').first()
print(f'Role: {user.role}')
"
```

2. If not admin, make yourself admin:
```bash
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.db.session import SessionLocal
from app.models.user import User
db = SessionLocal()
user = db.query(User).filter(User.email == 'YOUR_EMAIL').first()
user.role = 'admin'
db.commit()
print('User is now admin')
"
```

#### B. Frontend Not Rebuilt
**Solution:**
```bash
cd /home/deploy/apps/reddit-bot
git pull origin main
docker-compose -f docker-compose.prod.yml build --no-cache frontend
docker-compose -f docker-compose.prod.yml restart frontend
```

#### C. Browser Cache
**Solution:**
- Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
- Or open in incognito/private mode

---

### 3. No Client Dropdown in Configs

**This is NORMAL behavior!**

**Why:** The client dropdown only shows when:
- You are an admin user (`role === 'admin'`)
- AND you don't have a client_id assigned to your user

**Scenarios:**

#### Scenario A: Regular User (Has client_id)
- ✅ **Expected:** No client dropdown
- ✅ **Reason:** You're assigned to a specific client
- ✅ **Behavior:** Configs automatically use your client_id

#### Scenario B: Admin Without client_id
- ✅ **Expected:** Client dropdown appears
- ✅ **Reason:** You can create configs for any client
- ✅ **Behavior:** Must select a client from dropdown

#### Scenario C: Admin With client_id
- ✅ **Expected:** No client dropdown
- ✅ **Reason:** You're assigned to a specific client
- ✅ **Behavior:** Configs automatically use your client_id

**To See Client Dropdown:**
1. Be an admin user
2. Remove your client_id assignment:
```bash
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.db.session import SessionLocal
from app.models.user import User
db = SessionLocal()
user = db.query(User).filter(User.email == 'YOUR_EMAIL').first()
user.client_id = None
db.commit()
print('Client ID removed - you can now select any client')
"
```

---

### 4. Scanning Not Working

**Check Beat Container:**
```bash
docker-compose -f docker-compose.prod.yml ps beat
# Should show "Up" not "Restarting"

docker-compose -f docker-compose.prod.yml logs beat --tail=50
# Should see: "Scheduler: Sending due task scan-reddit-dynamic"
```

**If Beat is Restarting:**
```bash
# Check for permission errors
docker-compose -f docker-compose.prod.yml logs beat | grep -i error

# Restart beat
docker-compose -f docker-compose.prod.yml restart beat
```

**If No Scans Running:**
```bash
# Check if you have active configs
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.db.session import SessionLocal
from app.models.config import ClientConfig
db = SessionLocal()
configs = db.query(ClientConfig).filter(ClientConfig.is_active == True).all()
print(f'Active configs: {len(configs)}')
for cfg in configs:
    print(f'  - Client {cfg.client_id}: {cfg.reddit_subreddits}')
"
```

---

### 5. No Posts Appearing

**Check Reddit API Credentials:**
```bash
# Verify credentials are set
docker-compose -f docker-compose.prod.yml exec backend env | grep REDDIT

# Should see:
# REDDIT_CLIENT_ID=...
# REDDIT_CLIENT_SECRET=...
# REDDIT_USER_AGENT=...
```

**Test Reddit Connection:**
```bash
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.services.reddit_service import test_reddit_connection
result = test_reddit_connection()
print(result)
"
```

**Check Worker Logs:**
```bash
docker-compose -f docker-compose.prod.yml logs worker --tail=100
```

---

### 6. AI Responses Not Generating

**Check OpenAI API Key:**
```bash
docker-compose -f docker-compose.prod.yml exec backend env | grep OPENAI_API_KEY
```

**Test OpenAI Connection:**
```bash
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.services.openai_service import client
print('OpenAI client configured:', client is not None)
"
```

**Check for Fine-Tuned Model Access:**
```bash
# Check backend logs for OpenAI errors
docker-compose -f docker-compose.prod.yml logs backend | grep -i openai
```

---

### 7. Container Keeps Restarting

**Check Specific Container:**
```bash
# See which container is restarting
docker-compose -f docker-compose.prod.yml ps

# Check its logs
docker-compose -f docker-compose.prod.yml logs CONTAINER_NAME --tail=100
```

**Common Fixes:**

#### Backend Restarting:
```bash
# Check database connection
docker-compose -f docker-compose.prod.yml logs postgres --tail=50

# Check environment variables
docker-compose -f docker-compose.prod.yml exec backend env
```

#### Frontend Restarting:
```bash
# Rebuild frontend
docker-compose -f docker-compose.prod.yml build --no-cache frontend
docker-compose -f docker-compose.prod.yml restart frontend
```

#### Beat Restarting:
```bash
# Already fixed in docker-compose.prod.yml
# If still restarting, check logs:
docker-compose -f docker-compose.prod.yml logs beat --tail=100
```

---

### 8. Can't Login

**Check User Exists:**
```bash
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.db.session import SessionLocal
from app.models.user import User
db = SessionLocal()
user = db.query(User).filter(User.email == 'YOUR_EMAIL').first()
if user:
    print(f'User found: {user.email}')
    print(f'Role: {user.role}')
    print(f'Active: {user.is_active}')
else:
    print('User not found')
"
```

**Reset Password:**
```bash
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
db = SessionLocal()
user = db.query(User).filter(User.email == 'YOUR_EMAIL').first()
user.hashed_password = get_password_hash('NEW_PASSWORD')
db.commit()
print('Password reset successfully')
"
```

---

### 9. Database Issues

**Check Database Connection:**
```bash
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d redditbot -c "SELECT COUNT(*) FROM users;"
```

**Run Migrations:**
```bash
docker-compose -f docker-compose.prod.yml exec backend python -m app.scripts.db
```

**Backup Database:**
```bash
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres redditbot > backup_$(date +%Y%m%d).sql
```

---

### 10. Performance Issues

**Check Resource Usage:**
```bash
docker stats
```

**Check Logs for Errors:**
```bash
docker-compose -f docker-compose.prod.yml logs --tail=200 | grep -i error
```

**Restart All Services:**
```bash
docker-compose -f docker-compose.prod.yml restart
```

---

## 🚀 Complete Deployment Checklist

After pulling latest changes:

```bash
# 1. Navigate to project
cd /home/deploy/apps/reddit-bot

# 2. Pull latest code
git pull origin main

# 3. Rebuild services (if needed)
docker-compose -f docker-compose.prod.yml build --no-cache

# 4. Restart all services
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# 5. Check all containers are running
docker-compose -f docker-compose.prod.yml ps

# 6. Check logs for errors
docker-compose -f docker-compose.prod.yml logs --tail=50

# 7. Test the application
curl http://localhost:8000/api/health
curl http://localhost:3000
```

---

## 📞 Quick Diagnostic Commands

```bash
# Check all container status
docker-compose -f docker-compose.prod.yml ps

# Check all logs
docker-compose -f docker-compose.prod.yml logs --tail=100

# Check specific service
docker-compose -f docker-compose.prod.yml logs SERVICE_NAME --tail=50

# Restart specific service
docker-compose -f docker-compose.prod.yml restart SERVICE_NAME

# Rebuild specific service
docker-compose -f docker-compose.prod.yml build --no-cache SERVICE_NAME

# Check environment variables
docker-compose -f docker-compose.prod.yml exec SERVICE_NAME env

# Execute command in container
docker-compose -f docker-compose.prod.yml exec SERVICE_NAME COMMAND

# Check resource usage
docker stats

# Clean up unused resources
docker system prune -a
```

---

## ✅ Verification After Fixes

1. **Dates Display Correctly**
   - [ ] Post dates show: "Dec 10, 2025 02:30 PM"
   - [ ] Response dates show correctly
   - [ ] No "Invalid Date" or "Unknown date"

2. **Navigation Works**
   - [ ] Dashboard loads
   - [ ] Configs page loads
   - [ ] Clients page loads (admin only)
   - [ ] All links work

3. **Client Management**
   - [ ] Admin can see Clients link
   - [ ] Admin can create clients
   - [ ] Clients appear in config dropdown (if admin without client_id)

4. **Scanning Works**
   - [ ] Beat container is running (not restarting)
   - [ ] Scans run every minute
   - [ ] New posts appear in dashboard

5. **All Containers Healthy**
   - [ ] backend - Up (healthy)
   - [ ] frontend - Up (healthy)
   - [ ] worker - Up
   - [ ] beat - Up
   - [ ] postgres - Up (healthy)
   - [ ] redis - Up (healthy)
   - [ ] nginx - Up (healthy)

---

## 🎯 Current Status Summary

After all fixes:
- ✅ Dates display correctly (backend schema fixed)
- ✅ Clients link shows only for admins
- ✅ Client dropdown shows when appropriate
- ✅ 24/7 scanning configured
- ✅ No "Disconnected" status
- ✅ Fine-tuned AI model in use
- ✅ Collapsed responses by default
- ✅ Client filtering available
- ✅ Auto-scan on config creation

Your system is fully operational! 🚀
