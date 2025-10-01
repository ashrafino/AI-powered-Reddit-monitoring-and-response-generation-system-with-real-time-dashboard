# Complete Setup Guide

## Issues Fixed

1. **Frontend API Configuration**: Fixed incorrect API URL configuration that was causing 500 Internal Server Errors
2. **TypeScript Compilation Issues**: Resolved duplicate variable definitions in apiBase.ts
3. **Missing Configuration File**: Created the missing apiBase.ts file
4. **Port Conflicts**: Resolved port conflicts between services
5. **Background Task Processing**: Set up Redis and Celery for background task processing

## Services Running

1. **Backend API**: Running on http://localhost:8001
2. **Frontend**: Running on http://localhost:3002
3. **Redis**: Running on localhost:6379
4. **Celery Worker**: Processing background tasks
5. **Database**: SQLite database at ./dev.db

## Commands to Start Services

### 1. Start Redis (if not already running)
```bash
brew services start redis
```

### 2. Start Backend API
```bash
cd /Users/macbook/Documents/REDDIT\ BOT
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 3. Start Celery Worker
```bash
cd /Users/macbook/Documents/REDDIT\ BOT
source .venv/bin/activate
celery -A app.celery_app.celery_app worker --loglevel=INFO
```

### 4. Start Frontend
```bash
cd /Users/macbook/Documents/REDDIT\ BOT/frontend
npm run dev -- -p 3002
```

## Testing the Setup

### 1. Create a Test User
```bash
curl -X POST http://localhost:8001/api/auth/register -H "Content-Type: application/json" -d '{"email":"test@example.com","password":"test123","client_name":"Test Client","create_client_if_missing":true}'
```

### 2. Login and Get Token
```bash
curl -X POST http://localhost:8001/api/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d "username=test@example.com&password=test123"
```

### 3. Test API Endpoints
```bash
# Test posts endpoint
curl -X GET http://localhost:8001/api/posts/ -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Test scan endpoint
curl -X POST http://localhost:8001/api/ops/scan -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Accessing the Application

1. Visit http://localhost:3002 in your browser
2. Login with the test user credentials:
   - Email: test@example.com
   - Password: test123
3. The dashboard should load without errors

## Troubleshooting

### If you see 503 Service Unavailable errors:
1. Ensure Redis is running: `brew services start redis`
2. Ensure Celery worker is running
3. Check that no port conflicts exist

### If you see 401 Unauthorized errors:
1. Make sure you're logged in and have a valid token
2. Check that the token is being sent in the Authorization header

### If you see 500 Internal Server Errors:
1. Check that the API base URL is correctly configured in `/frontend/utils/apiBase.ts`
2. Ensure all services are running on the correct ports

## File Changes Made

1. **Created `/frontend/utils/apiBase.ts`**: Configured API base URL for development
2. **Updated API endpoint URLs**: Fixed frontend to correctly communicate with backend
3. **Resolved port conflicts**: Set up services on non-conflicting ports

## Docker Environment

The fixes maintain compatibility with the Docker environment:
- Environment variables still control API base URL in production
- Nginx routing configuration unchanged
- No impact on containerized deployment

## Future Improvements

1. **Automated Service Startup**: Create a script to start all services with one command
2. **Improved Error Handling**: Add more descriptive error messages in frontend
3. **Database Seeding**: Add sample data for development testing
4. **Environment Configuration**: Add development.env file for consistent local configuration