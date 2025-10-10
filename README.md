# 🤖 AI-Powered Reddit Monitoring & Response System

[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js_14-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL_15-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

A comprehensive AI-powered Reddit monitoring and response generation system with real-time dashboard, multi-client support, and enterprise-grade features.

**🔗 Repository:** [github.com/ashrafino/AI-powered-Reddit-monitoring-and-response-generation-system-with-real-time-dashboard](https://github.com/ashrafino/AI-powered-Reddit-monitoring-and-response-generation-system-with-real-time-dashboard)

---

## 📑 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [Services Overview](#-services-overview)
- [Configuration](#-configuration)
- [Production Deployment](#-production-deployment)
- [Development](#-development)
- [Monitoring & Analytics](#-monitoring--analytics)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)
- [Support & Resources](#-support--resources)

---

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

### Prerequisites

- Docker & Docker Compose
- Git
- OpenAI API Key
- Reddit API Credentials

### Development Setup

```bash
# 1. Clone repository
git clone https://github.com/ashrafino/AI-powered-Reddit-monitoring-and-response-generation-system-with-real-time-dashboard.git
cd AI-powered-Reddit-monitoring-and-response-generation-system-with-real-time-dashboard

# 2. Create environment file
cp .env.example .env

# 3. Edit .env with your credentials
nano .env  # or use your preferred editor

# 4. Start services
docker-compose up -d --build

# 5. Create admin user (first time only)
docker-compose exec backend python -c "
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
db = SessionLocal()
admin = User(
    email='admin@example.com',
    hashed_password=get_password_hash('admin123'),
    is_active=True,
    is_superuser=True
)
db.add(admin)
db.commit()
print('Admin user created!')
"

# 6. Access your application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8001
# API Docs: http://localhost:8001/docs
```

### Production Deployment

```bash
# 1. Set up production environment
cp .env.prod.example .env.prod
nano .env.prod  # Configure production settings

# 2. Deploy with production compose
docker-compose -f docker-compose.prod.yml up -d --build

# 3. Set up SSL (if using domain)
# See DIGITALOCEAN_DEPLOYMENT_GUIDE.md for complete setup
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
SECRET_KEY=your-super-secure-secret-key-here-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-key-different-from-secret-key

# Database
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/redditbot

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Reddit API (Get from https://www.reddit.com/prefs/apps)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=RedditBot/1.0

# OpenAI API (Get from https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-your-openai-api-key

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8001
```

**Getting API Keys:**

1. **Reddit API:**
   - Go to https://www.reddit.com/prefs/apps
   - Click "Create App" or "Create Another App"
   - Select "script" type
   - Copy Client ID and Secret

2. **OpenAI API:**
   - Visit https://platform.openai.com/api-keys
   - Create new secret key
   - Copy the key (shown only once)

### Advanced Configuration

See `.env.example` for all available options including:

- Email/SMTP settings
- Rate limiting configuration
- Monitoring and logging
- Performance tuning
- Security settings

## 🌐 Production Deployment

### DigitalOcean Deployment (Recommended)

Complete step-by-step guide for production deployment:

```bash
# 1. Create DigitalOcean Droplet
# - Ubuntu 22.04 LTS
# - Minimum: 2GB RAM, 2 vCPUs
# - Recommended: 4GB RAM, 2 vCPUs

# 2. SSH into server
ssh root@your-server-ip

# 3. Clone repository
git clone https://github.com/ashrafino/AI-powered-Reddit-monitoring-and-response-generation-system-with-real-time-dashboard.git
cd AI-powered-Reddit-monitoring-and-response-generation-system-with-real-time-dashboard

# 4. Run automated setup
chmod +x deploy-to-digitalocean.sh
./deploy-to-digitalocean.sh

# 5. Configure environment
nano .env.prod

# 6. Deploy
sudo docker-compose -f docker-compose.prod.yml up -d --build
```

**📖 Detailed Guide:** See [DIGITALOCEAN_DEPLOYMENT_GUIDE.md](./DIGITALOCEAN_DEPLOYMENT_GUIDE.md) for complete instructions including:
- SSL certificate setup
- Domain configuration
- Security hardening
- Monitoring setup
- Backup configuration

### Quick Production Deployment

```bash
# Production environment
cp .env.prod.example .env.prod
nano .env.prod  # Edit with production values

# Deploy with production compose
docker-compose -f docker-compose.prod.yml up -d --build

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## 🛠️ Development

### Local Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f worker

# Restart a service
docker-compose restart backend

# Rebuild after code changes
docker-compose up -d --build

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### Running Tests

```bash
# Backend tests
docker-compose exec backend pytest

# Frontend tests
docker-compose exec frontend npm test

# Type checking
docker-compose exec frontend npm run type-check
```

### Database Management

```bash
# Access PostgreSQL
docker-compose exec postgres psql -U postgres -d redditbot

# Create database backup
docker-compose exec postgres pg_dump -U postgres redditbot > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres redditbot < backup.sql

# Reset database
docker-compose down -v postgres
docker-compose up -d postgres
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

#### Services won't start

```bash
# Check logs for errors
docker-compose logs

# Check specific service
docker-compose logs backend

# Restart all services
docker-compose restart

# Clean rebuild
docker-compose down -v
docker-compose up --build -d
```

#### Database connection issues

```bash
# Check database status
docker-compose exec postgres pg_isready

# Check database logs
docker-compose logs postgres

# Reset database (WARNING: deletes all data)
docker-compose down -v postgres
docker-compose up -d postgres
```

#### Frontend not loading

```bash
# Check frontend logs
docker-compose logs frontend

# Rebuild frontend
docker-compose up -d --build frontend

# Check if port 3000 is available
lsof -i :3000  # macOS/Linux
netstat -ano | findstr :3000  # Windows
```

#### Backend API errors

```bash
# Check backend logs
docker-compose logs backend

# Check if backend is running
curl http://localhost:8001/health

# Restart backend
docker-compose restart backend
```

#### Celery worker not processing tasks

```bash
# Check worker logs
docker-compose logs worker

# Check Celery beat scheduler
docker-compose logs beat

# Restart workers
docker-compose restart worker beat
```

#### Port conflicts

```bash
# If ports are already in use, modify docker-compose.yml
# Change port mappings:
# "8001:8001" -> "8002:8001"  # Backend
# "3000:3000" -> "3001:3000"  # Frontend
```

#### Docker disk space issues

```bash
# Clean up Docker resources
docker system prune -f

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune
```

### Performance Optimization

```bash
# Check resource usage
docker stats

# Increase Docker memory (Docker Desktop)
# Settings -> Resources -> Memory: 4GB+

# Monitor database performance
docker-compose exec postgres psql -U postgres -d redditbot -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE state = 'active' 
ORDER BY duration DESC;
"
```

### Getting Help

1. **Check logs first:** `docker-compose logs -f`
2. **Review documentation:** Check relevant `.md` files
3. **Search issues:** [GitHub Issues](https://github.com/ashrafino/AI-powered-Reddit-monitoring-and-response-generation-system-with-real-time-dashboard/issues)
4. **Create new issue:** Include logs and error messages

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
   ```bash
   # Click "Fork" on GitHub
   git clone https://github.com/YOUR-USERNAME/AI-powered-Reddit-monitoring-and-response-generation-system-with-real-time-dashboard.git
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow code style guidelines
   - Add tests for new features
   - Update documentation

4. **Test your changes**
   ```bash
   # Backend tests
   docker-compose exec backend pytest
   
   # Frontend type checking
   docker-compose exec frontend npm run type-check
   ```

5. **Commit and push**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   git push origin feature/your-feature-name
   ```

6. **Submit a pull request**
   - Go to GitHub and create a PR
   - Describe your changes
   - Link any related issues

### Development Guidelines

- **Python:** Follow PEP 8 style guide
- **TypeScript:** Use strict type checking
- **Commits:** Use conventional commit messages
- **Tests:** Add tests for new features
- **Documentation:** Update relevant `.md` files

### Code Style

```bash
# Format Python code
docker-compose exec backend black app/

# Format TypeScript code
docker-compose exec frontend npm run format

# Lint code
docker-compose exec backend flake8 app/
docker-compose exec frontend npm run lint
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support & Resources

### Documentation

- **[DIGITALOCEAN_DEPLOYMENT_GUIDE.md](./DIGITALOCEAN_DEPLOYMENT_GUIDE.md)** - Complete production deployment guide
- **[TYPESCRIPT_SCAN_COMPLETE.md](./TYPESCRIPT_SCAN_COMPLETE.md)** - TypeScript codebase status
- **[API Documentation](http://localhost:8001/docs)** - Interactive API docs (when running)

### Getting Help

- **🐛 Bug Reports:** [Create an issue](https://github.com/ashrafino/AI-powered-Reddit-monitoring-and-response-generation-system-with-real-time-dashboard/issues/new?template=bug_report.md)
- **💡 Feature Requests:** [Create an issue](https://github.com/ashrafino/AI-powered-Reddit-monitoring-and-response-generation-system-with-real-time-dashboard/issues/new?template=feature_request.md)
- **❓ Questions:** [GitHub Discussions](https://github.com/ashrafino/AI-powered-Reddit-monitoring-and-response-generation-system-with-real-time-dashboard/discussions)

### Useful Commands

```bash
# Check service health
curl http://localhost:8001/health

# View all running containers
docker-compose ps

# Check Docker resource usage
docker stats

# View application logs
docker-compose logs -f --tail=100

# Access backend shell
docker-compose exec backend bash

# Access frontend shell
docker-compose exec frontend sh

# Access database
docker-compose exec postgres psql -U postgres -d redditbot
```

## 🎯 Roadmap

### In Progress
- [ ] WebSocket real-time updates (backend implementation)
- [ ] Enhanced monitoring dashboard
- [ ] Performance optimization

### Planned Features
- [ ] Advanced AI model integration (GPT-4, Claude)
- [ ] Multi-language support
- [ ] Mobile application (React Native)
- [ ] Browser extension for quick responses
- [ ] Integration with Discord, Twitter, LinkedIn
- [ ] Advanced user role management
- [ ] Automated testing suite
- [ ] CI/CD pipeline

### Future Enhancements
- [ ] Machine learning for response optimization
- [ ] A/B testing for responses
- [ ] Sentiment analysis
- [ ] Competitor monitoring
- [ ] Custom AI model training

**Want to contribute?** Check out our [Contributing](#-contributing) section!

## 🎥 Demo & Screenshots

### 🖥️ Dashboard Overview
![Dashboard](https://via.placeholder.com/800x400?text=Real-Time+Dashboard+Screenshot)
*Real-time monitoring dashboard with live updates and analytics*

### 💬 Response Management
![Response Management](https://via.placeholder.com/800x400?text=AI+Response+Management+Screenshot)
*AI-generated responses with inline editing, preview, and quality scoring*

### 📊 Analytics & Insights
![Analytics](https://via.placeholder.com/800x400?text=Analytics+Dashboard+Screenshot)
*Comprehensive analytics with keyword tracking and performance metrics*

### 🔧 Configuration Management
![Configuration](https://via.placeholder.com/800x400?text=Configuration+Management+Screenshot)
*Easy-to-use configuration interface for monitoring settings*

> **Note:** Replace placeholder images with actual screenshots from your deployment. Store images in a `docs/images/` folder and update the links.

### 🎬 Video Demo

*Coming soon - Add a video walkthrough of the system*

---

## 🔐 Security

### Security Best Practices

- **Never commit `.env` files** - Already in `.gitignore`
- **Use strong secrets** - Generate with `openssl rand -hex 32`
- **Rotate API keys regularly** - Especially after team changes
- **Enable HTTPS in production** - Use Let's Encrypt (free)
- **Keep dependencies updated** - Run `docker-compose pull` regularly
- **Monitor logs** - Check for suspicious activity
- **Backup database** - Regular automated backups

### Reporting Security Issues

If you discover a security vulnerability, please email security@example.com instead of using the issue tracker.

---

## 📊 Project Stats

- **Backend:** FastAPI + Python 3.11
- **Frontend:** Next.js 14 + TypeScript
- **Database:** PostgreSQL 15
- **Cache:** Redis 7
- **Task Queue:** Celery
- **Deployment:** Docker + Docker Compose
- **Code Quality:** TypeScript strict mode, Python type hints

---

## ❓ FAQ

### General Questions

**Q: Does this bot automatically post to Reddit?**  
A: No. This system generates AI responses but requires manual review and posting to ensure compliance with Reddit's terms of service.

**Q: What AI model does it use?**  
A: Currently uses OpenAI's GPT models. You can configure which model to use in the environment variables.

**Q: Can I monitor multiple subreddits?**  
A: Yes! You can configure multiple subreddits and keywords per client configuration.

**Q: Is this free to use?**  
A: The software is free and open-source (MIT License), but you'll need API keys for Reddit and OpenAI which may have costs.

### Technical Questions

**Q: What are the minimum server requirements?**  
A: Minimum 2GB RAM, 2 vCPUs. Recommended: 4GB RAM, 2 vCPUs for production.

**Q: Can I use this without Docker?**  
A: While possible, Docker is highly recommended for easier deployment and dependency management.

**Q: How do I backup my data?**  
A: Use `docker-compose exec postgres pg_dump -U postgres redditbot > backup.sql` for database backups.

**Q: Can I customize the AI responses?**  
A: Yes! You can modify the prompt templates in the backend code and adjust quality scoring parameters.

**Q: Does it support multiple users/clients?**  
A: Yes! The system has built-in multi-tenant support with user authentication and client isolation.

### Troubleshooting

**Q: Services won't start, what should I do?**  
A: Check logs with `docker-compose logs`, ensure ports aren't in use, and verify your `.env` file is configured correctly.

**Q: How do I reset everything?**  
A: Run `docker-compose down -v` to stop and remove all containers and volumes, then rebuild with `docker-compose up --build -d`.

---

## 🌟 Star History

If you find this project useful, please consider giving it a star! ⭐

[![Star History Chart](https://api.star-history.com/svg?repos=ashrafino/AI-powered-Reddit-monitoring-and-response-generation-system-with-real-time-dashboard&type=Date)](https://star-history.com/#ashrafino/AI-powered-Reddit-monitoring-and-response-generation-system-with-real-time-dashboard&Date)

---

## 📝 Changelog

See [CHANGELOG.md](./CHANGELOG.md) for version history and updates.

---

## 👥 Authors

- **Ashraf** - *Initial work* - [@ashrafino](https://github.com/ashrafino)

See also the list of [contributors](https://github.com/ashrafino/AI-powered-Reddit-monitoring-and-response-generation-system-with-real-time-dashboard/contributors) who participated in this project.

---

## 🙏 Acknowledgments

- OpenAI for GPT API
- Reddit for PRAW API
- FastAPI community
- Next.js team
- All contributors and users

---

**⚠️ Compliance Notice**: This system does NOT automatically post to Reddit. All responses require manual review and posting by operators to ensure compliance with Reddit's terms of service and community guidelines.

---

**Made with ❤️ by the community**
