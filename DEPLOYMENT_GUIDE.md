# 🚀 DigitalOcean Deployment Guide

Complete guide to deploy your Reddit Bot System to DigitalOcean with production-ready configuration.

## 📋 Prerequisites

- DigitalOcean account
- Domain name (recommended)
- Reddit API credentials
- OpenAI API key
- Basic knowledge of SSH and command line

## 🏗️ Step 1: Create DigitalOcean Droplet

### Recommended Specifications
- **Size**: 2 GB RAM / 1 vCPU / 50 GB SSD ($12/month)
- **OS**: Ubuntu 22.04 LTS
- **Region**: Choose closest to your users
- **Additional Options**: 
  - Enable monitoring
  - Add SSH key for secure access

### Create Droplet
1. Log into DigitalOcean
2. Click "Create" → "Droplets"
3. Choose Ubuntu 22.04 LTS
4. Select $12/month plan (2GB RAM)
5. Add your SSH key
6. Create droplet

## 🔧 Step 2: Initial Server Setup

### Connect to Your Server
```bash
ssh root@your-server-ip
```

### Create Non-Root User
```bash
adduser deploy
usermod -aG sudo deploy
su - deploy
```

### Run Setup Script
```bash
# Download and run the setup script
curl -fsSL https://raw.githubusercontent.com/your-repo/reddit-bot-system/main/deploy/digitalocean-setup.sh -o setup.sh
chmod +x setup.sh
./setup.sh
```

This script will:
- Install Docker and Docker Compose
- Configure firewall and security
- Set up monitoring and backups
- Create necessary directories
- Configure systemd services

## 📁 Step 3: Deploy Your Application

### Clone Repository
```bash
cd /opt/reddit-bot
git clone https://github.com/your-username/reddit-bot-system.git .
```

### Configure Environment
```bash
# Copy and edit production environment file
cp .env.prod.example .env.prod
nano .env.prod
```

**Required Environment Variables:**
```bash
# Domain
DOMAIN_NAME=your-domain.com

# Database
POSTGRES_PASSWORD=your-secure-password

# Redis
REDIS_PASSWORD=your-secure-redis-password

# App Security
SECRET_KEY=your-32-character-secret-key

# Admin
ADMIN_EMAIL=admin@your-domain.com
ADMIN_PASSWORD=your-admin-password

# Reddit API
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=RedditBot/1.0

# OpenAI
OPENAI_API_KEY=your_openai_api_key
```

## 🌐 Step 4: Configure Domain and DNS

### Point Domain to Server
1. Go to your domain registrar
2. Add A records:
   - `@` → `your-server-ip`
   - `www` → `your-server-ip`

### Wait for DNS Propagation
```bash
# Check DNS propagation
dig your-domain.com
nslookup your-domain.com
```

## 🔒 Step 5: Set Up SSL Certificate

### Run SSL Setup Script
```bash
sudo ./deploy/ssl-setup.sh your-domain.com admin@your-domain.com
```

This will:
- Install Let's Encrypt certificate
- Configure nginx for HTTPS
- Set up automatic renewal

## 🚀 Step 6: Deploy Application

### Build and Start Services
```bash
# Make deploy script executable
chmod +x deploy.sh

# Deploy the application
./deploy.sh
```

### Verify Deployment
```bash
# Check service status
sudo systemctl status reddit-bot

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Check running containers
docker ps
```

## 🔍 Step 7: Verify Everything Works

### Test Endpoints
```bash
# Health check
curl https://your-domain.com/health

# API health
curl https://your-domain.com/api/health

# Frontend
curl -I https://your-domain.com
```

### Access Your Application
- **Frontend**: https://your-domain.com
- **API**: https://your-domain.com/api
- **Admin Login**: Use credentials from .env.prod

## 📊 Step 8: Monitoring and Maintenance

### View Logs
```bash
# Application logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Nginx logs
sudo tail -f /var/log/nginx/access.log

# System logs
sudo journalctl -u reddit-bot -f
```

### Monitor Resources
```bash
# System resources
htop

# Docker stats
docker stats

# Disk usage
df -h
```

### Backup Management
```bash
# Manual backup
./backup.sh

# View backups
ls -la backups/

# Restore from backup (if needed)
# Instructions in backup files
```

## 🔄 Step 9: Updates and Maintenance

### Deploy Updates
```bash
cd /opt/reddit-bot
git pull origin main
./deploy.sh
```

### Scale Services (if needed)
```bash
# Scale backend workers
docker-compose -f docker-compose.prod.yml up -d --scale worker=3

# Scale frontend
docker-compose -f docker-compose.prod.yml up -d --scale frontend=2
```

## 🛠️ Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Rebuild if needed
docker-compose -f docker-compose.prod.yml build --no-cache
```

#### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew manually
sudo /opt/reddit-bot/renew-ssl.sh

# Test nginx config
sudo nginx -t
```

#### Database Connection Issues
```bash
# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres

# Connect to database
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d redditbot
```

#### High Memory Usage
```bash
# Check memory usage
free -h

# Restart services to free memory
docker-compose -f docker-compose.prod.yml restart

# Clean up unused Docker resources
docker system prune -f
```

### Performance Optimization

#### Enable Swap (if needed)
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

#### Optimize Docker
```bash
# Clean up regularly
docker system prune -f --volumes

# Limit log sizes (already configured in daemon.json)
# Monitor with: docker system df
```

## 📈 Scaling Considerations

### Vertical Scaling (Upgrade Droplet)
1. Power off droplet
2. Resize in DigitalOcean panel
3. Power on and verify

### Horizontal Scaling (Multiple Servers)
- Use DigitalOcean Load Balancer
- Separate database to managed PostgreSQL
- Use Redis cluster
- Consider Docker Swarm or Kubernetes

## 🔐 Security Best Practices

### Regular Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose -f docker-compose.prod.yml pull
./deploy.sh
```

### Monitor Security
```bash
# Check fail2ban status
sudo fail2ban-client status

# Review firewall rules
sudo ufw status

# Check for suspicious activity
sudo tail -f /var/log/auth.log
```

## 📞 Support

### Useful Commands
```bash
# Service management
sudo systemctl status reddit-bot
sudo systemctl restart reddit-bot

# View all logs
docker-compose -f docker-compose.prod.yml logs --tail=100

# Database backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres redditbot > backup.sql

# Emergency stop
docker-compose -f docker-compose.prod.yml down
```

### Getting Help
- Check logs first: `docker-compose logs`
- Review this guide
- Check DigitalOcean documentation
- Monitor resource usage with `htop`

---

## 🎉 Congratulations!

Your Reddit Bot System is now deployed and running in production on DigitalOcean!

**What's Next?**
- Set up monitoring alerts
- Configure additional Reddit accounts
- Customize AI response templates
- Set up automated testing
- Consider CDN for better performance

**Remember:**
- Monitor your usage and costs
- Keep your API keys secure
- Regular backups are automated
- SSL certificates auto-renew
- Check logs regularly for issues