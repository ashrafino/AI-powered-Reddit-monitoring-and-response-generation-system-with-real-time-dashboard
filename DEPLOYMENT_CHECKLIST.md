# 📋 DigitalOcean Deployment Checklist

Use this checklist to ensure you don't miss any steps during deployment.

## Pre-Deployment

### Accounts & Services
- [ ] DigitalOcean account created
- [ ] Domain name purchased (optional)
- [ ] Reddit API credentials obtained
- [ ] OpenAI API key obtained
- [ ] SerpAPI key obtained
- [ ] YouTube API key obtained
- [ ] GitHub repository created (optional)

### Local Preparation
- [ ] SSH key pair generated (`ssh-keygen`)
- [ ] Code committed to Git
- [ ] `.env.prod.example` reviewed
- [ ] All API keys documented

## DigitalOcean Setup

### Droplet Creation
- [ ] Droplet created (Ubuntu 22.04 LTS)
- [ ] Size selected (minimum 2GB RAM)
- [ ] SSH key added
- [ ] IP address noted: `___________________`
- [ ] Firewall configured (ports 22, 80, 443)

### Initial Server Access
- [ ] SSH connection successful: `ssh root@YOUR_IP`
- [ ] System updated: `apt update && apt upgrade -y`
- [ ] Non-root user created: `deploy`
- [ ] SSH keys copied to deploy user
- [ ] Firewall enabled: `ufw enable`

## Software Installation

### Docker Setup
- [ ] Docker installed
- [ ] Docker Compose installed
- [ ] User added to docker group
- [ ] Docker verified: `docker --version`
- [ ] Docker Compose verified: `docker-compose --version`

### Application Setup
- [ ] Repository cloned to `~/apps/reddit-bot`
- [ ] `.env` file created from template
- [ ] All environment variables filled in:
  - [ ] `SECRET_KEY` (generated)
  - [ ] `POSTGRES_PASSWORD` (generated)
  - [ ] `REDIS_PASSWORD` (generated)
  - [ ] `ADMIN_EMAIL` and `ADMIN_PASSWORD`
  - [ ] `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`
  - [ ] `OPENAI_API_KEY`
  - [ ] `SERPAPI_API_KEY`
  - [ ] `YOUTUBE_API_KEY`
  - [ ] `FRONTEND_API_BASE`

## Deployment

### Build & Start
- [ ] Docker images built successfully
- [ ] All services started: `docker-compose -f docker-compose.prod.yml up -d`
- [ ] Services running: `docker ps` shows 6 containers
- [ ] Backend health check passes: `curl http://localhost/api/health`
- [ ] Frontend accessible: `curl http://localhost`

### Database Setup
- [ ] Database initialized
- [ ] Admin user created
- [ ] Tables created: `docker-compose exec postgres psql -U postgres -d redditbot -c "\dt"`

### Service Verification
- [ ] Backend logs clean: `docker-compose logs backend`
- [ ] Worker logs clean: `docker-compose logs worker`
- [ ] Beat logs clean: `docker-compose logs beat`
- [ ] Frontend logs clean: `docker-compose logs frontend`
- [ ] Nginx logs clean: `docker-compose logs nginx`

## Domain & SSL (Optional but Recommended)

### Domain Configuration
- [ ] Domain DNS A record points to droplet IP
- [ ] DNS propagation verified: `dig yourdomain.com`
- [ ] Domain accessible: `http://yourdomain.com`

### SSL Certificate
- [ ] Certbot installed
- [ ] SSL certificate obtained
- [ ] Certificates copied to project
- [ ] Nginx configured for HTTPS
- [ ] HTTPS working: `https://yourdomain.com`
- [ ] HTTP redirects to HTTPS
- [ ] Auto-renewal cron job added

## Testing

### Application Testing
- [ ] Can access login page
- [ ] Can log in with admin credentials
- [ ] Dashboard loads correctly
- [ ] Can view configs page
- [ ] Can create new config
- [ ] "Scan now" button works
- [ ] Posts appear after scan
- [ ] AI responses generated
- [ ] Analytics display correctly

### API Testing
- [ ] `/api/health` returns 200
- [ ] `/api/auth/login` works
- [ ] `/api/posts` returns data
- [ ] `/api/configs` returns data
- [ ] `/api/analytics/summary` returns data
- [ ] `/api/ops/scan` triggers scan

## Monitoring & Maintenance

### Backup Setup
- [ ] Database backup script created
- [ ] Backup cron job added
- [ ] Test backup: `~/backup-db.sh`
- [ ] Backup directory exists: `~/backups`

### Monitoring
- [ ] Can view logs: `docker-compose logs -f`
- [ ] Can check status: `docker-compose ps`
- [ ] Disk space monitored: `df -h`
- [ ] Memory monitored: `free -h`

### Documentation
- [ ] Server IP documented
- [ ] Admin credentials saved securely
- [ ] Database passwords saved securely
- [ ] API keys documented
- [ ] Deployment date noted: `___________________`

## Security

### Server Security
- [ ] SSH password authentication disabled
- [ ] Firewall configured and enabled
- [ ] Fail2ban installed and configured
- [ ] System updates automated
- [ ] Non-root user used for deployment

### Application Security
- [ ] Strong passwords used for all services
- [ ] Environment variables not committed to Git
- [ ] SSL/HTTPS enabled
- [ ] API keys kept secret
- [ ] Admin password changed from default

## Post-Deployment

### Final Checks
- [ ] Application accessible from external network
- [ ] All features working as expected
- [ ] No errors in logs
- [ ] Performance acceptable
- [ ] Mobile responsive
- [ ] SSL certificate valid

### Team Handoff
- [ ] Deployment guide shared
- [ ] Credentials shared securely
- [ ] Monitoring access provided
- [ ] Support contacts documented

## Troubleshooting Reference

If something goes wrong:

1. **Check logs**: `docker-compose -f docker-compose.prod.yml logs -f`
2. **Check status**: `docker-compose -f docker-compose.prod.yml ps`
3. **Restart services**: `docker-compose -f docker-compose.prod.yml restart`
4. **Rebuild**: `docker-compose -f docker-compose.prod.yml up -d --build`
5. **Check resources**: `docker stats`

## Quick Commands

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart all services
docker-compose -f docker-compose.prod.yml restart

# Update application
cd ~/apps/reddit-bot
git pull
docker-compose -f docker-compose.prod.yml up -d --build

# Backup database
~/backup-db.sh

# Check disk space
df -h

# Check memory
free -h
```

---

## Completion

- [ ] All checklist items completed
- [ ] Application deployed successfully
- [ ] Team notified
- [ ] Documentation updated

**Deployment Date**: ___________________

**Deployed By**: ___________________

**Server IP**: ___________________

**Domain**: ___________________

---

**🎉 Congratulations on your successful deployment!**
