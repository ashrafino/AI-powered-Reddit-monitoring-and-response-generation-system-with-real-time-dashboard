# 🚀 Quick Deploy Reference Card

## One-Page Deployment Guide

### 1️⃣ Create DigitalOcean Droplet (5 min)
```
Size: $12/month (2GB RAM)
OS: Ubuntu 22.04 LTS
Add SSH key
Note IP: ___________________
```

### 2️⃣ Initial Server Setup (10 min)
```bash
# SSH into server
ssh root@YOUR_IP

# Update & install essentials
apt update && apt upgrade -y
apt install -y curl git ufw

# Create user
adduser deploy
usermod -aG sudo deploy
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy

# Configure firewall
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Switch user
su - deploy
```

### 3️⃣ Install Docker (5 min)
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again
exit
ssh deploy@YOUR_IP
```

### 4️⃣ Clone & Configure (10 min)
```bash
# Clone repository
mkdir -p ~/apps && cd ~/apps
git clone YOUR_REPO_URL reddit-bot
cd reddit-bot

# Create .env file
cp .env.prod.example .env
nano .env

# Generate secure passwords
openssl rand -hex 32  # SECRET_KEY
openssl rand -base64 32  # POSTGRES_PASSWORD
openssl rand -base64 32  # REDIS_PASSWORD
```

### 5️⃣ Deploy (5 min)
```bash
# Build and start
docker-compose -f docker-compose.prod.yml up -d --build

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 6️⃣ Verify (2 min)
```bash
# Test backend
curl http://localhost/api/health

# Test frontend
curl http://localhost

# Get your IP
curl ifconfig.me
```

**Access**: `http://YOUR_IP`

---

## Essential Commands

### Daily Operations
```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart service
docker-compose -f docker-compose.prod.yml restart backend

# Check status
docker-compose -f docker-compose.prod.yml ps

# Update app
git pull && docker-compose -f docker-compose.prod.yml up -d --build
```

### Troubleshooting
```bash
# Restart all
docker-compose -f docker-compose.prod.yml restart

# Rebuild all
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# Check resources
docker stats
df -h
free -h
```

### Database
```bash
# Backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres redditbot > backup.sql

# Restore
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U postgres redditbot < backup.sql

# Access
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d redditbot
```

---

## SSL Setup (Optional - 15 min)

### Point Domain
```
Add A Record:
Host: @
Value: YOUR_DROPLET_IP
```

### Install Certificate
```bash
# Install Certbot
sudo apt install -y certbot

# Stop nginx
docker-compose -f docker-compose.prod.yml stop nginx

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates
sudo mkdir -p ~/apps/reddit-bot/ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ~/apps/reddit-bot/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ~/apps/reddit-bot/ssl/
sudo chown -R deploy:deploy ~/apps/reddit-bot/ssl

# Update nginx.prod.conf for HTTPS
# Then restart
docker-compose -f docker-compose.prod.yml restart nginx
```

---

## Environment Variables Checklist

```bash
# Required
SECRET_KEY=                    # openssl rand -hex 32
POSTGRES_PASSWORD=             # openssl rand -base64 32
REDIS_PASSWORD=                # openssl rand -base64 32
ADMIN_EMAIL=
ADMIN_PASSWORD=

# API Keys
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
OPENAI_API_KEY=
SERPAPI_API_KEY=
YOUTUBE_API_KEY=

# Frontend
FRONTEND_API_BASE=http://YOUR_IP  # or https://yourdomain.com
```

---

## Cost Breakdown

```
DigitalOcean Droplet: $12-24/month
Domain (optional): $10-15/year
SSL: Free (Let's Encrypt)

API Usage:
- OpenAI: ~$10-50/month
- SerpAPI: $50/month
- YouTube: Free

Total: ~$75-125/month
```

---

## Support

- **Full Guide**: See `DIGITALOCEAN_DEPLOYMENT_GUIDE.md`
- **Checklist**: See `DEPLOYMENT_CHECKLIST.md`
- **Logs**: `docker-compose -f docker-compose.prod.yml logs -f`
- **Status**: `docker-compose -f docker-compose.prod.yml ps`

---

## Emergency Contacts

```
DigitalOcean Support: https://cloud.digitalocean.com/support
Server IP: ___________________
Admin Email: ___________________
Deployed: ___________________
```

---

**Total Time: ~45 minutes** ⏱️

**Difficulty: Intermediate** 📊

**Prerequisites: SSH key, API keys, Domain (optional)** 🔑
