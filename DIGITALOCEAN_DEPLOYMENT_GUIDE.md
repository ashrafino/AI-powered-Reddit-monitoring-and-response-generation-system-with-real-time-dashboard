# 🚀 Complete DigitalOcean Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [DigitalOcean Setup](#digitalocean-setup)
3. [Server Configuration](#server-configuration)
4. [Application Deployment](#application-deployment)
5. [Domain & SSL Setup](#domain--ssl-setup)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Accounts
- ✅ DigitalOcean account
- ✅ Domain name (optional but recommended)
- ✅ GitHub account (for code repository)

### Required API Keys
- ✅ Reddit API credentials
- ✅ OpenAI API key
- ✅ SerpAPI key (for Google search)
- ✅ YouTube API key

### Local Requirements
- ✅ SSH key pair
- ✅ Git installed
- ✅ Basic terminal knowledge

---

## DigitalOcean Setup

### Step 1: Create a Droplet

1. **Log in to DigitalOcean**
   - Go to https://cloud.digitalocean.com

2. **Create New Droplet**
   - Click "Create" → "Droplets"

3. **Choose Configuration**
   ```
   Region: Choose closest to your users (e.g., New York, San Francisco)
   Image: Ubuntu 22.04 LTS x64
   Droplet Type: Basic
   CPU Options: Regular
   Size: 
     - Minimum: $12/month (2 GB RAM, 1 vCPU, 50 GB SSD)
     - Recommended: $18/month (2 GB RAM, 2 vCPU, 60 GB SSD)
     - Production: $24/month (4 GB RAM, 2 vCPU, 80 GB SSD)
   ```

4. **Add SSH Key**
   - Click "New SSH Key"
   - Paste your public key (`cat ~/.ssh/id_rsa.pub`)
   - Name it (e.g., "My Laptop")

5. **Finalize**
   - Hostname: `reddit-bot-prod`
   - Tags: `production`, `reddit-bot`
   - Click "Create Droplet"

6. **Note Your IP Address**
   - Copy the droplet's IP address (e.g., `164.90.xxx.xxx`)

### Step 2: Configure Firewall

1. **Go to Networking → Firewalls**
2. **Create Firewall**
   ```
   Name: reddit-bot-firewall
   
   Inbound Rules:
   - SSH: TCP, Port 22, All IPv4, All IPv6
   - HTTP: TCP, Port 80, All IPv4, All IPv6
   - HTTPS: TCP, Port 443, All IPv4, All IPv6
   
   Outbound Rules:
   - All TCP, All Ports, All IPv4, All IPv6
   - All UDP, All Ports, All IPv4, All IPv6
   ```
3. **Apply to Droplet**
   - Select your droplet
   - Click "Create Firewall"

---

## Server Configuration

### Step 1: Initial Server Setup

```bash
# SSH into your server
ssh root@YOUR_DROPLET_IP

# Update system
apt update && apt upgrade -y

# Install essential packages
apt install -y curl git wget vim ufw fail2ban

# Configure firewall
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Create non-root user
adduser deploy
usermod -aG sudo deploy

# Copy SSH keys to new user
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy

# Switch to deploy user
su - deploy
```

### Step 2: Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version

# Log out and back in for group changes
exit
ssh deploy@YOUR_DROPLET_IP
```

### Step 3: Clone Your Repository

```bash
# Create app directory
mkdir -p ~/apps
cd ~/apps

# Clone your repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git reddit-bot
cd reddit-bot

# Or if using SSH
git clone git@github.com:YOUR_USERNAME/YOUR_REPO.git reddit-bot
```

---

## Application Deployment

### Step 1: Configure Environment Variables

```bash
# Copy production environment template
cp .env.prod.example .env

# Edit environment file
nano .env
```

**Fill in your `.env` file:**

```bash
# Application
APP_ENV=production
API_PREFIX=/api
SECRET_KEY=$(openssl rand -hex 32)  # Generate secure key
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database
POSTGRES_PASSWORD=$(openssl rand -base64 32)  # Generate secure password
DATABASE_URL=postgresql://postgres:YOUR_POSTGRES_PASSWORD@postgres/redditbot

# Redis
REDIS_PASSWORD=$(openssl rand -base64 32)  # Generate secure password
REDIS_URL=redis://:YOUR_REDIS_PASSWORD@redis:6379/0
CELERY_BROKER_URL=redis://:YOUR_REDIS_PASSWORD@redis:6379/1
CELERY_RESULT_BACKEND=redis://:YOUR_REDIS_PASSWORD@redis:6379/1

# Admin User
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=YOUR_SECURE_ADMIN_PASSWORD

# Frontend
FRONTEND_API_BASE=https://yourdomain.com  # Or http://YOUR_DROPLET_IP

# Reddit API
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=RedditBot/1.0

# OpenAI
OPENAI_API_KEY=sk-proj-your-openai-key

# SerpAPI (Google Search)
SERPAPI_API_KEY=your_serpapi_key

# YouTube
YOUTUBE_API_KEY=your_youtube_api_key

# Email (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com

# Monitoring (Optional)
SENTRY_DSN=your-sentry-dsn
```

**Generate secure passwords:**
```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate POSTGRES_PASSWORD
openssl rand -base64 32

# Generate REDIS_PASSWORD
openssl rand -base64 32
```

### Step 2: Configure Nginx

```bash
# Edit nginx configuration
nano nginx.prod.conf
```

**Update with your domain or IP:**

```nginx
upstream backend {
    server backend:8001;
}

upstream frontend {
    server frontend:3000;
}

server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;  # Change this!
    
    client_max_body_size 10M;
    
    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Backend API
    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

### Step 3: Build and Deploy

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d --build

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Check specific service
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f worker
```

### Step 4: Verify Deployment

```bash
# Check if services are running
docker ps

# Test backend health
curl http://localhost/api/health

# Test frontend
curl http://localhost

# Check database
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d redditbot -c "\dt"

# Check Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli -a YOUR_REDIS_PASSWORD ping
```

---

## Domain & SSL Setup

### Step 1: Point Domain to Droplet

1. **In Your Domain Registrar (e.g., Namecheap, GoDaddy)**
   ```
   Add A Record:
   Type: A
   Host: @
   Value: YOUR_DROPLET_IP
   TTL: 300
   
   Add A Record (for www):
   Type: A
   Host: www
   Value: YOUR_DROPLET_IP
   TTL: 300
   ```

2. **Wait for DNS Propagation** (5-30 minutes)
   ```bash
   # Check DNS propagation
   dig yourdomain.com
   nslookup yourdomain.com
   ```

### Step 2: Install SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Stop nginx temporarily
docker-compose -f docker-compose.prod.yml stop nginx

# Get SSL certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Certificates will be saved to:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem

# Copy certificates to project
sudo mkdir -p ~/apps/reddit-bot/ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ~/apps/reddit-bot/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ~/apps/reddit-bot/ssl/
sudo chown -R deploy:deploy ~/apps/reddit-bot/ssl
```

### Step 3: Update Nginx for HTTPS

```bash
# Edit nginx configuration
nano ~/apps/reddit-bot/nginx.prod.conf
```

**Add SSL configuration:**

```nginx
upstream backend {
    server backend:8001;
}

upstream frontend {
    server frontend:3000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    client_max_body_size 10M;
    
    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Backend API
    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

### Step 4: Restart Services

```bash
cd ~/apps/reddit-bot

# Restart nginx
docker-compose -f docker-compose.prod.yml restart nginx

# Or restart all services
docker-compose -f docker-compose.prod.yml restart

# Verify HTTPS
curl https://yourdomain.com
```

### Step 5: Auto-Renew SSL Certificate

```bash
# Test renewal
sudo certbot renew --dry-run

# Add cron job for auto-renewal
sudo crontab -e

# Add this line (runs twice daily):
0 0,12 * * * certbot renew --quiet --post-hook "cp /etc/letsencrypt/live/yourdomain.com/*.pem ~/apps/reddit-bot/ssl/ && cd ~/apps/reddit-bot && docker-compose -f docker-compose.prod.yml restart nginx"
```

---

## Monitoring & Maintenance

### Daily Operations

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Check service status
docker-compose -f docker-compose.prod.yml ps

# Restart a service
docker-compose -f docker-compose.prod.yml restart backend

# Update application
cd ~/apps/reddit-bot
git pull
docker-compose -f docker-compose.prod.yml up -d --build
```

### Database Backup

```bash
# Create backup script
nano ~/backup-db.sh
```

```bash
#!/bin/bash
BACKUP_DIR=~/backups
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

cd ~/apps/reddit-bot
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U postgres redditbot > $BACKUP_DIR/backup_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete

echo "Backup completed: backup_$DATE.sql"
```

```bash
# Make executable
chmod +x ~/backup-db.sh

# Add to crontab (daily at 2 AM)
crontab -e
0 2 * * * ~/backup-db.sh
```

### Monitor Resources

```bash
# Check disk space
df -h

# Check memory
free -h

# Check Docker stats
docker stats

# Check logs size
du -sh ~/apps/reddit-bot/logs
```

### Update Application

```bash
cd ~/apps/reddit-bot

# Pull latest code
git pull

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Check specific service
docker-compose -f docker-compose.prod.yml logs backend

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Rebuild from scratch
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

### Database Issues

```bash
# Access database
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d redditbot

# Check tables
\dt

# Check connections
SELECT * FROM pg_stat_activity;

# Reset database (CAUTION!)
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d
```

### High Memory Usage

```bash
# Check memory
free -h

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Reduce worker concurrency
# Edit docker-compose.prod.yml:
# Change: --concurrency=2 to --concurrency=1
```

### SSL Certificate Issues

```bash
# Renew certificate manually
sudo certbot renew

# Copy to project
sudo cp /etc/letsencrypt/live/yourdomain.com/*.pem ~/apps/reddit-bot/ssl/

# Restart nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### Can't Access Application

```bash
# Check if services are running
docker ps

# Check nginx logs
docker-compose -f docker-compose.prod.yml logs nginx

# Check firewall
sudo ufw status

# Test locally
curl http://localhost
curl http://localhost/api/health
```

---

## Cost Estimation

### Monthly Costs

```
DigitalOcean Droplet: $12-24/month
Domain Name: $10-15/year
SSL Certificate: Free (Let's Encrypt)

API Costs (usage-based):
- OpenAI API: ~$10-50/month
- SerpAPI: $50/month (5,000 searches)
- YouTube API: Free (10,000 requests/day)

Total: ~$75-125/month
```

---

## Security Checklist

- ✅ Use strong passwords for all services
- ✅ Enable firewall (UFW)
- ✅ Use SSH keys (disable password auth)
- ✅ Keep system updated
- ✅ Use HTTPS/SSL
- ✅ Regular backups
- ✅ Monitor logs
- ✅ Use environment variables for secrets
- ✅ Enable fail2ban
- ✅ Limit API rate limits

---

## Quick Reference Commands

```bash
# Start services
docker-compose -f docker-compose.prod.yml up -d

# Stop services
docker-compose -f docker-compose.prod.yml down

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart service
docker-compose -f docker-compose.prod.yml restart backend

# Update code
git pull && docker-compose -f docker-compose.prod.yml up -d --build

# Backup database
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres redditbot > backup.sql

# Restore database
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U postgres redditbot < backup.sql

# Check status
docker-compose -f docker-compose.prod.yml ps

# Access container
docker-compose -f docker-compose.prod.yml exec backend bash
```

---

## Support & Resources

- **DigitalOcean Docs**: https://docs.digitalocean.com
- **Docker Docs**: https://docs.docker.com
- **Let's Encrypt**: https://letsencrypt.org
- **Your App Logs**: `docker-compose logs -f`

---

**🎉 Congratulations! Your Reddit Bot is now deployed on DigitalOcean!**

Access your application at: `https://yourdomain.com` or `http://YOUR_DROPLET_IP`
