# Runtime API Detection Solution

## Problem
The frontend was hardcoding `localhost:8001` during build time, causing connection errors when deployed to production servers with different IPs.

## Solution
Implemented **runtime API base URL detection** that automatically adapts to any environment without hardcoding IPs.

## How It Works

### 1. Runtime Detection Logic (`frontend/utils/runtimeConfig.ts`)
```typescript
- Development (localhost): Uses http://localhost:8001
- Production (any IP/domain): Uses relative URLs (empty string)
- Nginx proxies /api/* to backend automatically
```

### 2. Benefits
✅ **No hardcoded IPs** - Works on any server IP or domain
✅ **Automatic detection** - Detects environment at runtime in browser
✅ **No rebuild needed** - Changing server IP doesn't require rebuild
✅ **Nginx proxy** - Uses relative URLs that nginx routes to backend
✅ **Debug logging** - Console logs show detected configuration

### 3. How Requests Work

**Development:**
```
Browser → http://localhost:8001/api/auth/login → Backend
```

**Production (any IP like 146.190.50.85):**
```
Browser → /api/auth/login → Nginx → http://backend:8001/api/auth/login
```

### 4. Deployment Steps

```bash
# On your server
cd /home/deploy/apps/reddit-bot

# Rebuild frontend with new detection logic
sudo docker-compose -f docker-compose.prod.yml build frontend --no-cache

# Restart services
sudo docker-compose -f docker-compose.prod.yml up -d

# Check logs
sudo docker-compose -f docker-compose.prod.yml logs -f frontend
```

### 5. Verification

Open browser console and you should see:
```
Production mode: using relative URLs (nginx proxy)
API Base URL detected: (relative URLs)
Current hostname: 146.190.50.85
```

### 6. Configuration Override (Optional)

If you ever need to override the detection:
```bash
# In docker-compose.prod.yml, add:
environment:
  - NEXT_PUBLIC_API_BASE=http://your-custom-url
```

But with this solution, you shouldn't need to!

## Technical Details

- **Runtime detection** happens in browser using `window.location.hostname`
- **No build-time baking** of URLs into JavaScript bundles
- **SSR compatible** - Server-side rendering uses relative URLs
- **Backward compatible** - Existing code continues to work
