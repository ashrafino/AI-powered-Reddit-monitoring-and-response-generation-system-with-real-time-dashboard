# 🤖 Reddit Bot System

A comprehensive AI-powered Reddit monitoring and response generation system with real-time dashboard, multi-client support, and enterprise-grade features.

## ✨ Features

### 🎯 Core Functionality

- **AI-Powered Response Generation** - OpenAI integration for intelligent Reddit responses
- **Real-Time Monitoring** - Live Reddit post tracking with WebSocket updates
- **Multi-Client Support** - Secure multi-tenant architecture
- **Manual Approval Workflow** - Compliance-focused, no auto-posting
- **Advanced Analytics** - Comprehensive performance tracking and insights

### 🖥️ Dashboard Features

- **Real-Time Updates** - Live WebSocket-powered dashboard
- **Response Management** - Inline editing, preview, and version history
- **Advanced Search & Filtering** - Multi-criteria post and response filtering
- **Mobile Responsive** - Fully functional on all devices
- **Performance Monitoring** - Built-in performance metrics and optimization

### 🔒 Security & Compliance

- **JWT Authentication** - Secure token-based authentication
- **Rate Limiting** - API protection and abuse prevention
- **HTTPS/SSL** - Production-ready security
- **Audit Logging** - Comprehensive activity tracking
- **Manual-Only Posting** - No automated Reddit posting for compliance

### 📊 Analytics & Insights

- **Interactive Charts** - Real-time analytics visualization
- **Keyword Performance** - Track keyword effectiveness
- **Subreddit Analytics** - Performance by community
- **Quality Scoring** - AI response quality assessment
- **Growth Tracking** - Performance trends over time

## 🚀 Quick Start

### Development (Fastest)

```bash
# Clone repository
git clone https://github.com/your-username/reddit-bot-system.git
cd reddit-bot-system

# Quick development setup (no Docker builds!)
./scripts/fast-build.sh

# Access your application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8001
# API Docs: http://localhost:8001/docs
```

### Production Docker

```bash
# Copy environment file
cp .env.example .env
# Edit .env with your API keys and settings

# Build and run
docker-compose up --build -d

# Access via Nginx proxy
# Application: http://localhost
```

## 🏗️ Architecture

### Backend Services

- **FastAPI Backend** - High-performance Python API
- **Celery Workers** - Distributed task processing
- **Celery Beat** - Scheduled task management
- **PostgreSQL** - Primary database
- **Redis** - Caching and message broker
- **WebSocket Server** - Real-time communication

### Frontend

- **Next.js** - React-based frontend application
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Modern responsive design
- **SWR** - Data fetching and caching
- **WebSocket Client** - Real-time updates

### Infrastructure

- **Nginx** - Reverse proxy and load balancer
- **Docker** - Containerized deployment
- **SSL/TLS** - Automatic HTTPS with Let's Encrypt
- **Monitoring** - Health checks and performance tracking

## 📦 Services Overview

| Service    | Description                | Port   |
| ---------- | -------------------------- | ------ |
| `backend`  | FastAPI application server | 8001   |
| `worker`   | Celery background worker   | -      |
| `beat`     | Celery task scheduler      | -      |
| `frontend` | Next.js web application    | 3000   |
| `postgres` | PostgreSQL database        | 5432   |
| `redis`    | Redis cache/message broker | 6379   |
| `nginx`    | Reverse proxy              | 80/443 |

## 🔧 Configuration

### Environment Variables

Create a `.env` file from the template:

```bash
cp .env.example .env
```

**Required Configuration:**

```bash
# Application Security
SECRET_KEY=your-super-secure-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key

# Database
DATABASE_URL=postgresql://postgres:password@postgres/redditbot

# Redis
REDIS_URL=redis://redis:6379/0

# Reddit API
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=RedditBot/1.0

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# Admin User
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=secure_password
```

### Advanced Configuration

See `.env.example` for all available options including:

- Email/SMTP settings
- Rate limiting configuration
- Monitoring and logging
- Performance tuning
- Security settings

## 🌐 Production Deployment

### DigitalOcean (Recommended)

Complete production deployment with SSL, monitoring, and backups:

```bash
# See detailed guide
cat DEPLOYMENT_GUIDE.md

# Quick deployment
./deploy/digitalocean-setup.sh
```

**Features:**

- Automated server setup
- SSL certificate management
- Security hardening
- Monitoring and alerting
- Automated backups
- Performance optimization

### Manual Deployment

```bash
# Production environment
cp .env.prod.example .env.prod
# Edit with production values

# Deploy with production compose
docker-compose -f docker-compose.prod.yml up -d --build
```

## 🛠️ Development

### Local Development

```bash
# Fast development mode (recommended)
./scripts/fast-build.sh

# Traditional Docker development
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose logs -f backend
```

### Code Structure

```
├── app/                    # Backend Python application
│   ├── api/               # API routes and endpoints
│   ├── core/              # Core configuration and security
│   ├── models/            # Database models
│   ├── services/          # Business logic services
│   └── celery_app/        # Celery configuration
├── frontend/              # Next.js frontend application
│   ├── components/        # React components
│   ├── pages/            # Next.js pages
│   ├── utils/            # Utility functions
│   └── styles/           # CSS and styling
├── deploy/               # Deployment scripts and configs
├── nginx/                # Nginx configurations
└── scripts/              # Build and utility scripts
```

### API Documentation

- **Interactive Docs**: http://localhost:8001/docs
- **OpenAPI Schema**: http://localhost:8001/openapi.json
- **ReDoc**: http://localhost:8001/redoc

## 📊 Monitoring & Analytics

### Built-in Monitoring

- **Health Checks** - Service availability monitoring
- **Performance Metrics** - Response times and resource usage
- **Error Tracking** - Comprehensive error logging
- **Usage Analytics** - User activity and API usage

### Dashboard Analytics

- **Real-time Charts** - Live performance visualization
- **Keyword Tracking** - Monitor keyword effectiveness
- **Subreddit Performance** - Community-specific analytics
- **Quality Metrics** - AI response quality scoring

## 🔍 Troubleshooting

### Common Issues

**Services won't start:**

```bash
# Check logs
docker-compose logs

# Restart services
docker-compose restart

# Clean rebuild
docker-compose down -v
docker-compose up --build
```

**Database connection issues:**

```bash
# Check database status
docker-compose exec postgres pg_isready

# Reset database
docker-compose down -v postgres
docker-compose up -d postgres
```

**Performance issues:**

```bash
# Enable performance monitoring
# In dashboard: Click "Perf ON" button

# Check resource usage
docker stats

# Clean up Docker resources
docker system prune -f
```

### Build Optimization

If builds are slow, use the optimized development mode:

```bash
# Fast development (no Docker builds)
./scripts/fast-build.sh

# See build optimization guide
cat BUILD_OPTIMIZATION.md
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Guidelines

- Follow Python PEP 8 style guide
- Use TypeScript for frontend development
- Add tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check the guides in this repository
- **Issues**: Create a GitHub issue for bugs or feature requests
- **Deployment**: See `DEPLOYMENT_GUIDE.md` for production setup
- **Performance**: See `BUILD_OPTIMIZATION.md` for build improvements

## 🎯 Roadmap

- [ ] Advanced AI model integration
- [ ] Multi-language support
- [ ] Enhanced analytics dashboard
- [ ] Mobile application
- [ ] API rate limiting improvements
- [ ] Advanced user management
- [ ] Integration with more social platforms

---

### Environment variables

Create a `.env` file in the project root. Do NOT commit it.

Copy-paste template:

```bash
# Application
APP_ENV=development
API_PREFIX=/api
SECRET_KEY=change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database
DATABASE_URL=postgresql+psycopg://postgres:postgres@postgres:5432/redditbot

# Redis / Celery
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# OpenAI
OPENAI_API_KEY=

# Reddit API (PRAW)
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=RedditAnalyzer/1.0

# SERP API
SERPAPI_API_KEY=

# YouTube Data API (optional)
YOUTUBE_API_KEY=

# SMTP / Email (optional)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
EMAIL_FROM=

# Observability (optional)
SENTRY_DSN=
```

Security notes:

- Keep `.env` out of version control. Add `.env` to `.gitignore`.
- Never share real keys in issues/PRs. Use placeholders in examples.
- Rotate keys if you suspect exposure.

---

**⚠️ Compliance Notice**: This system does NOT automatically post to Reddit. All responses require manual review and posting by operators to ensure compliance with Reddit's terms of service and community guidelines.
