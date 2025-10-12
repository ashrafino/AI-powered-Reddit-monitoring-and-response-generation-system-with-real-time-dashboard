# Complete Deployment with Date Fix

## The Problem

The backend container is running OLD code that doesn't include `created_at` in the API responses. We need to:
1. Pull latest code (has schema with created_at)
2. Rebuild backend (not just restart)
3. Rebuild frontend (has date formatting)
4. Restart everything

## 🚀 Complete Deployment Commands

Run these on your server:

```bash
cd /home/deploy/apps/reddit-bot

# 1. Pull latest code
git pull origin main

# 2. Rebuild BOTH backend and frontend
docker-compose -f docker-compose.prod.yml build --no-cache backend frontend

# 3. Restart everything
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# 4. Wait for services to start
sleep 15

# 5. Check all containers are running
docker-compose -f docker-compose.prod.yml ps

# 6. Verify backend has new schema
docker-compose -f docker-compose.prod.yml exec backend cat app/schemas/post.py | grep "created_at"

# 7. Check logs for any errors
docker-compose -f docker-compose.prod.yml logs --tail=50
```

## ✅ Verification

After deployment, test the API:

```bash
# Get a token first (login to the app and copy from browser dev tools)
# Then test:
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/posts/ | python3 -m json.tool | grep -A 2 "created_at"

# Should show:
# "created_at": "2025-10-12T13:49:27.123456+00:00",
```

## 🧪 In Browser

After deployment:
1. **Logout** from the app
2. **Login** again
3. **Hard refresh** (Ctrl+Shift+R or Cmd+Shift+R)
4. **Check dashboard** - dates should show: "Oct 12, 2025 01:49 PM"
5. **Check responses** - dates should show correctly
6. **Check scanning status** - should show active configs
7. **Click Clients** - should work (no redirect)

## 📊 What You'll See

### Dashboard:
```
┌─────────────────────┬─────────────────────┬─────────────────────┐
│ Total Posts Found   │ AI Responses Gen.   │ Scanning Status     │
│ 150                 │ 450                 │ 🟢 Active (Every 5m)│
│                     │                     │ Monitoring:         │
│                     │                     │ r/webdev, r/coding  │
│                     │                     │ Keywords: API, bot  │
└─────────────────────┴─────────────────────┴─────────────────────┘

Posts:
┌────────────────────────────────────────────────────────────┐
│ r/webdev • Oct 12, 2025 01:49 PM          [Open on Reddit]│
│ How to build a Reddit bot?                                 │
│ Keywords: bot, API                                         │
│ ▶ AI Response (Score: 85, Grade: A-)                      │
└────────────────────────────────────────────────────────────┘
```

## 🐛 If Dates Still Don't Show

### Check 1: Backend has new code
```bash
docker-compose -f docker-compose.prod.yml exec backend cat app/schemas/post.py | grep "created_at"
# Should show: created_at: datetime
```

### Check 2: API returns created_at
```bash
# Login to app, get token from browser dev tools (Application > Local Storage > token)
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/posts/ | head -c 1000
# Should see "created_at" in the JSON
```

### Check 3: Frontend has new code
```bash
docker-compose -f docker-compose.prod.yml exec frontend cat /app/.next/BUILD_ID
# Should show today's date
```

### Check 4: Browser cache
- Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
- Or open in incognito mode

## 🎯 Why This Will Work

1. **Backend rebuild** - Gets new schema with created_at
2. **Frontend rebuild** - Gets date formatting code
3. **Full restart** - Ensures all containers use new code
4. **Logout/login** - Gets new token with admin role
5. **Hard refresh** - Clears browser cache

## ⚠️ Important Notes

- **Don't skip the rebuild** - Restart alone won't work
- **Must rebuild BOTH** backend and frontend
- **Must logout/login** - For admin access to work
- **Must hard refresh** - To clear browser cache

## 📝 Expected Timeline

- Pull code: 5 seconds
- Build backend: 2-3 minutes
- Build frontend: 2-3 minutes
- Restart services: 30 seconds
- Total: ~6 minutes

## ✅ Success Indicators

After deployment:
- ✅ All containers show "Up" or "Healthy"
- ✅ Backend logs show no errors
- ✅ Frontend logs show "Ready in XXXXms"
- ✅ Dates display correctly in browser
- ✅ Clients page accessible
- ✅ Scanning status visible

Run the commands above and everything will work! 🚀
