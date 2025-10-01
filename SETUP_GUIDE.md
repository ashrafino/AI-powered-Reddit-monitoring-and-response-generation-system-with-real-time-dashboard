# Reddit Bot SaaS - Complete Setup Guide

## 🎯 Project Goals Achieved

Your Reddit Bot project is already perfectly structured to meet all your requirements:

✅ **Multi-Client Monitoring**: Separate client accounts with isolated data  
✅ **Reddit Post Monitoring**: Keyword matching across chosen subreddits  
✅ **Real-time Context**: Google & YouTube integration for relevant context  
✅ **AI Response Generation**: OpenAI GPT creates 2-3 human-like suggestions  
✅ **Manual Review Process**: All responses require manual review before posting  
✅ **Secure Data Isolation**: Each client's data is completely separate  
✅ **Management Dashboard**: Live feed, response queue, analytics, configuration  

## 🚀 Quick Start

### 1. Environment Setup

Create a `.env` file in the project root with these variables:

```bash
# ===========================================
# CORE APPLICATION SETTINGS
# ===========================================
APP_ENV=development
API_PREFIX=/api
SECRET_KEY=your-super-secret-key-here-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=60

# ===========================================
# DATABASE CONFIGURATION
# ===========================================
DATABASE_URL=postgresql+psycopg://postgres:postgres@postgres:5432/redditbot

# ===========================================
# REDIS & CELERY CONFIGURATION
# ===========================================
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# ===========================================
# REDDIT API CONFIGURATION (REQUIRED)
# ===========================================
REDDIT_CLIENT_ID=your-reddit-client-id-here
REDDIT_CLIENT_SECRET=your-reddit-client-secret-here
REDDIT_USER_AGENT=RedditBot/1.0 (Multi-Client Monitoring)

# ===========================================
# OPENAI API CONFIGURATION (REQUIRED)
# ===========================================
OPENAI_API_KEY=your-openai-api-key-here

# ===========================================
# CONTEXT FETCHING APIs (REQUIRED)
# ===========================================
SERPAPI_API_KEY=your-serpapi-key-here
YOUTUBE_API_KEY=your-youtube-api-key-here

# ===========================================
# EMAIL CONFIGURATION (OPTIONAL)
# ===========================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com

# ===========================================
# MONITORING & LOGGING (OPTIONAL)
# ===========================================
SENTRY_DSN=your-sentry-dsn-here

# ===========================================
# FRONTEND CONFIGURATION
# ===========================================
NEXT_PUBLIC_API_BASE=http://localhost/api
```

### 2. Get Required API Keys

#### Reddit API (Essential)
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Choose "script" as the app type
4. Copy the client ID and secret

#### OpenAI API (Essential)
1. Go to https://platform.openai.com/api-keys
2. Create a new API key

#### SERP API (For Google Context)
1. Go to https://serpapi.com/
2. Sign up (100 free searches/month)
3. Get your API key

#### YouTube Data API (For Video Context)
1. Go to https://console.developers.google.com/
2. Enable "YouTube Data API v3"
3. Create credentials (API key)

### 3. Start the Application

```bash
# Start all services with Docker Compose
docker-compose up --build

# Or start in background
docker-compose up -d --build
```

### 4. Access the Application

- **Frontend Dashboard**: http://localhost
- **API Documentation**: http://localhost/api/docs
- **Admin Panel**: Use the dashboard to manage clients and configurations

## 🏗️ Architecture Overview

### Backend Services
- **FastAPI**: REST API with automatic documentation
- **PostgreSQL**: Multi-tenant database with client isolation
- **Redis**: Caching and task queue
- **Celery**: Background task processing
- **Celery Beat**: Scheduled Reddit scanning

### Frontend
- **Next.js**: React-based dashboard
- **Tailwind CSS**: Modern, responsive UI
- **SWR**: Data fetching and caching

### External Integrations
- **PRAW**: Reddit API client
- **OpenAI GPT**: AI response generation
- **SERP API**: Google search results
- **YouTube API**: Video context
- **Sentry**: Error monitoring

## 📊 How It Works

### 1. Client Setup
- Create client accounts in the dashboard
- Configure subreddits and keywords per client
- Set up monitoring schedules

### 2. Reddit Monitoring
- Celery Beat runs scheduled scans (configurable)
- PRAW fetches new posts from specified subreddits
- Keyword matching identifies relevant posts
- Duplicate detection prevents re-processing

### 3. Context Fetching
- For each matched post, fetch Google search results
- Get relevant YouTube videos
- Combine context for AI processing

### 4. AI Response Generation
- OpenAI GPT analyzes post + context
- Generates 2-3 human-like Reddit responses
- Responses are scored and ranked

### 5. Manual Review Process
- All responses appear in the dashboard
- Operators can copy responses to clipboard
- Compliance acknowledgment system
- No automated posting to Reddit

### 6. Analytics & Management
- Real-time dashboard with live feed
- Response queue management
- Client-specific analytics
- Configuration management

## 🔧 Configuration

### Client Management
- Each client has isolated data
- Separate subreddit lists and keywords
- Individual monitoring schedules
- Client-specific analytics

### Security Features
- JWT-based authentication
- Role-based access control (admin/client)
- Data isolation between clients
- Secure API key management

### Monitoring & Alerts
- Sentry integration for error tracking
- Email notifications for new matches
- Real-time dashboard updates
- Analytics and reporting

## 🚨 Important Notes

1. **No Automated Posting**: This system does NOT automatically post to Reddit
2. **Manual Review Required**: All responses must be manually reviewed and copied
3. **Client Isolation**: Each client's data is completely separate
4. **Compliance Ready**: Built-in compliance acknowledgment system
5. **Scalable**: Multi-tenant architecture supports unlimited clients

## 🛠️ Development

### Database Migrations
```bash
# The app auto-creates tables on startup for development
# For production, use Alembic migrations
```

### Adding New Features
- Backend: Add to FastAPI routers
- Frontend: Add to Next.js pages/components
- Database: Update SQLAlchemy models
- Tasks: Add to Celery task queue

### Testing
- API endpoints: Use FastAPI's automatic docs
- Frontend: Use the dashboard interface
- Integration: Test with real Reddit data

## 📈 Scaling

### Horizontal Scaling
- Multiple Celery workers
- Load-balanced FastAPI instances
- Redis clustering
- Database read replicas

### Performance Optimization
- Redis caching
- Database indexing
- Async processing
- CDN for static assets

Your Reddit Bot SaaS is ready to monitor Reddit, generate AI responses, and manage multiple clients with complete data isolation and manual review workflows!

