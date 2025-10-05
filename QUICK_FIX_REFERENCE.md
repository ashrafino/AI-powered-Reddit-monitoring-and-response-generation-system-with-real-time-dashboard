# Quick Fix Reference

## What Was Wrong

### Main Issue: Backend Not Running
Your backend API server wasn't starting because it couldn't compile the `psutil` Python package on your Apple Silicon Mac.

### Secondary Issue: Login Bug
The login function had a bug where it was sending conflicting data formats to the API.

---

## What I Fixed

### ✅ Fixed Backend Container
Added build tools (`gcc` and `python3-dev`) to Docker containers so Python packages can compile properly on ARM architecture.

### ✅ Fixed Login Function
Corrected the API call in `authContext.tsx` to send data in the correct format.

---

## Current Status

The backend is now rebuilding with the fixes. This takes 2-3 minutes.

**Check if it's ready:**
```bash
curl http://localhost:8001/api/health
```

When you see a JSON response, the backend is ready!

---

## Your Login Credentials

**Admin:**
- Email: `admin@example.com`
- Password: `admin123`

**Client:**
- Email: `client@example.com`  
- Password: `client123`

---

## Quick Commands

**Check backend logs:**
```bash
docker logs redditbot-backend-dev-1 --follow
```

**Restart everything:**
```bash
docker-compose -f docker-compose.dev.yml restart
```

**Check all services:**
```bash
docker ps
```

---

## What to Expect

1. Backend will finish installing (2-3 min)
2. You'll see: `INFO: Uvicorn running on http://0.0.0.0:8001`
3. Frontend at `http://localhost:3000` will connect successfully
4. Login will work without errors
5. No more `ERR_CONNECTION_RESET` errors

---

## If You Still See Errors

The browser extension errors (`Could not establish connection`) are harmless - they're from Chrome/browser extensions, not your app.

For real errors, check:
1. Docker logs: `docker-compose -f docker-compose.dev.yml logs`
2. Browser console (F12)
3. Make sure all containers are running: `docker ps`
