# Fix 400 Bad Request - Complete Deployment Guide

## What We Fixed

1. ✅ **Runtime API Detection** - No more hardcoded IPs
2. ✅ **CORS Configuration** - Backend now accepts requests through nginx proxy
3. 🔍 **Diagnostic Tools** - Scripts to identify the exact 400 error cause

## Deployment Steps

### Step 1: Push Changes (Local Machine)

```bash
# Add all changes
git add app/main.py
git add frontend/utils/runtimeConfig.ts
git add frontend/utils/apiBase.ts
git add docker-compose.prod.yml
git add DEBUG_400_ERROR.md
git add QUICK_FIX_400.sh
git add FIX_400_DEPLOYMENT.md

# Commit
git commit -m "Fix: CORS config and add 400 error diagnostics"

# Push
git push origin main
```

### Step 2: Deploy on Server

```bash
# SSH into server
ssh root@146.190.50.85

# Navigate to app directory
cd /home/deploy/apps/reddit-bot

# Pull latest changes
git pull origin main

# Make scripts executable
chmod +x QUICK_FIX_400.sh

# Run diagnostic script
./QUICK_FIX_400.sh
```

### Step 3: Rebuild Backend (if needed)

If the diagnostic shows CORS issues:

```bash
# Rebuild backend with new CORS settings
sudo docker-compose -f docker-compose.prod.yml build backend --no-cache

# Restart backend
sudo docker-compose -f docker-compose.prod.yml up -d backend

# Wait for it to be healthy
sudo docker-compose -f docker-compose.prod.yml ps backend
```

### Step 4: Test in Browser

1. Open: `http://146.190.50.85`
2. Open DevTools (F12) → Network tab
3. Try to login with:
   - Email: `admin@example.com`
   - Password: `admin123`
4. Check the `/api/auth/login` request:
   - **Status should be 200**
   - **Response should have access_token**

### Step 5: If Still Getting 400

Run this in browser console to see the exact error:

```javascript
fetch("/api/auth/login", {
  method: "POST",
  headers: {
    "Content-Type": "application/x-www-form-urlencoded",
  },
  body: new URLSearchParams({
    username: "admin@example.com",
    password: "admin123",
  }).toString(),
})
  .then(async (r) => {
    console.log("Status:", r.status);
    const data = await r.json();
    console.log("Response:", data);
    return data;
  })
  .catch(console.error);
```

## Common Issues & Solutions

### Issue 1: Admin User Doesn't Exist

**Symptom:** 400 with "Email and password are required"

**Fix:**

```bash
sudo docker-compose -f docker-compose.prod.yml exec backend python -m app.scripts.create_admin
```

### Issue 2: Wrong Password

**Symptom:** 401 with "Incorrect email or password"

**Fix:** Check your `.env` file:

```bash
cat .env | grep ADMIN_PASSWORD
```

Should match what you're entering in the login form.

### Issue 3: Request Body Not Reaching Backend

**Symptom:** 400 with "Email and password are required" even though you're sending them

**Fix:** Check nginx is not buffering/stripping the body:

```bash
# Add to nginx.prod.conf under location /api/
proxy_request_buffering off;
proxy_buffering off;

# Then restart nginx
sudo docker-compose -f docker-compose.prod.yml restart nginx
```

### Issue 4: CORS Preflight Failing

**Symptom:** OPTIONS request fails before POST

**Fix:** Already fixed in app/main.py - just rebuild backend

## Verification Checklist

- [ ] API detection shows "Production mode: using relative URLs"
- [ ] Login request goes to `/api/auth/login` (not `localhost:8001`)
- [ ] Request has `Content-Type: application/x-www-form-urlencoded`
- [ ] Request body contains `username` and `password`
- [ ] Backend logs show the request arriving
- [ ] Response status is 200
- [ ] Response contains `access_token`

## Still Need Help?

Share these outputs:

```bash
# 1. Backend logs
sudo docker-compose -f docker-compose.prod.yml logs --tail=50 backend

# 2. Nginx logs
sudo docker-compose -f docker-compose.prod.yml logs --tail=30 nginx

# 3. Container status
sudo docker-compose -f docker-compose.prod.yml ps

# 4. Test results
./QUICK_FIX_400.sh
```

And from browser DevTools:

- Screenshot of Network tab showing the failed request
- Request Headers
- Request Payload
- Response body
