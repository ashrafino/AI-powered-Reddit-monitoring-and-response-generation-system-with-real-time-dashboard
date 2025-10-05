# Reddit Bot Deployment Guide for Digital Ocean

## Prerequisites

1. **Digital Ocean Droplet** with at least 2GB RAM (4GB recommended)
2. **Ubuntu 22.04 LTS** or similar
3. **Docker and Docker Compose** installed
4. **Domain name** (optional, for SSL)

## Quick Setup

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Logout and login again for group changes to take effect
```

### 2. Clone and Configure

```bash
# Clone your repository
git clone <your-repo-url>
cd reddit-bot

# Copy and configure environment
cp .env.prod.example .env
nano .env  # Edit with your actual values
```

### 3. Deploy

```bash
# Make deploy script executable
chmod +x deploy.sh

# Deploy the application
./deploy.sh
```

## Production Deployment

For production, use the production docker-compose file:

```bash
# Deploy with production configuration
docker-compose -f docker-compose.prod.yml up --build -d
```

## Configuration

### Required Environment Variables

Edit `.env` file with your actual values:

```bash
# Security
SECRET_KEY=your-very-secure-secret-key-change-this
POSTGRES_PASSWORD=your-secure-postgres-password
REDIS_PASSWORD=your-secure-redis-password

# Admin User
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=your-secure-admin-password

# API Keys
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret
OPENAI_API_KEY=your-openai-api-key
SERPAPI_API_KEY=your-serpapi-key
YOUTUBE_API_KEY=your-youtube-api-key
```

### SSL/HTTPS Setup (Optional)

1. **Get SSL Certificate** (Let's Encrypt recommended):
```bash
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com
```

2. **Copy certificates**:
```bash
sudo mkdir -p ./ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./ssl/key.pem
sudo chown -R $USER:$USER ./ssl
```

3. **Update nginx configuration** in `nginx.prod.conf` (uncomment SSL section)

## Monitoring and Maintenance

### Check Service Status
```bash
docker-compose ps
docker-compose logs -f [service_name]
```

### Update Application
```bash
git pull
docker-compose down
docker-compose up --build -d
```

### Backup Database
```bash
docker-compose exec postgres pg_dump -U postgres redditbot > backup.sql
```

### Restore Database
```bash
docker-compose exec -T postgres psql -U postgres redditbot < backup.sql
```

## Troubleshooting

### Common Issues

1. **Login fails with 401**:
   - Check admin user was created: `docker-compose logs backend | grep admin`
   - Verify environment variables are correct

2. **WebSocket connection fails**:
   - Check nginx configuration includes WebSocket headers
   - Verify backend is accessible

3. **Database connection fails**:
   - Check PostgreSQL is running: `docker-compose ps postgres`
   - Verify DATABASE_URL format

4. **Frontend shows API errors**:
   - Check NEXT_PUBLIC_API_BASE environment variable
   - Verify nginx is proxying correctly

### Logs
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

## Performance Optimization

### For Production:
1. Increase worker processes in backend service
2. Enable nginx caching
3. Use Redis for session storage
4. Set up database connection pooling
5. Configure log rotation

### Resource Requirements:
- **Minimum**: 2GB RAM, 1 CPU, 20GB storage
- **Recommended**: 4GB RAM, 2 CPU, 40GB storage
- **High Traffic**: 8GB RAM, 4 CPU, 100GB storage

## Security Checklist

- [ ] Change all default passwords
- [ ] Use strong SECRET_KEY
- [ ] Enable SSL/HTTPS
- [ ] Configure firewall (UFW)
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity
- [ ] Backup database regularly

## Support

If you encounter issues:
1. Check the logs first
2. Verify environment variables
3. Test individual services
4. Check network connectivity
5. Review Digital Ocean droplet resources