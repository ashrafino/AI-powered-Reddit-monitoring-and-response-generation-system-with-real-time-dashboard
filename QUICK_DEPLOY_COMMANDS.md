# 🚀 Quick Deploy Commands

**One-page reference for deploying your updates**

---

## 📦 Deploy Documentation Updates to GitHub

### Option 1: All Files (Recommended)

```bash
# Add all documentation files
git add README.md \
        CHANGELOG.md \
        TYPESCRIPT_SCAN_COMPLETE.md \
        README_UPDATE_SUMMARY.md \
        GITHUB_DEPLOYMENT_CHECKLIST.md \
        DOCUMENTATION_COMPLETE.md \
        QUICK_DEPLOY_COMMANDS.md \
        frontend/pages/configs.tsx

# Commit
git commit -m "docs: Complete documentation overhaul and TypeScript fixes

- Fix TypeScript error in configs.tsx
- Comprehensive README with professional badges
- Add CHANGELOG.md and deployment guides
- Update all repository links
- Add FAQ and troubleshooting sections"

# Push
git push origin main
```

### Option 2: Quick One-Liner

```bash
git add . && git commit -m "docs: Complete documentation update" && git push origin main
```

---

## 🌐 Deploy to Production Server

### After Git Push

```bash
# SSH into server
ssh root@your-server-ip

# Navigate to project
cd /root/redditbot

# Pull latest changes
git pull origin main

# Rebuild frontend (includes TypeScript fix)
sudo docker-compose -f docker-compose.prod.yml build frontend --no-cache

# Restart services
sudo docker-compose -f docker-compose.prod.yml up -d

# Check status
sudo docker-compose -f docker-compose.prod.yml ps

# View logs
sudo docker-compose -f docker-compose.prod.yml logs -f frontend --tail=50
```

### One-Liner for Server

```bash
ssh root@your-server-ip "cd /root/redditbot && git pull origin main && sudo docker-compose -f docker-compose.prod.yml build frontend --no-cache && sudo docker-compose -f docker-compose.prod.yml up -d && sudo docker-compose -f docker-compose.prod.yml logs frontend --tail=20"
```

---

## ✅ Verify Deployment

### Check GitHub

```bash
# Open in browser
open https://github.com/ashrafino/AI-powered-Reddit-monitoring-and-response-generation-system-with-real-time-dashboard
```

Verify:
- ✅ README displays correctly
- ✅ Badges render
- ✅ Links work
- ✅ Code blocks formatted

### Check Production Server

```bash
# Check frontend health
curl -I http://your-server-ip:3000

# Or with domain
curl -I https://your-domain.com

# Check backend health
curl http://your-server-ip:8001/health
```

---

## 🔧 Quick Fixes

### If Frontend Won't Start

```bash
# On server
sudo docker-compose -f docker-compose.prod.yml logs frontend
sudo docker-compose -f docker-compose.prod.yml restart frontend
```

### If Build Fails

```bash
# Clean rebuild
sudo docker-compose -f docker-compose.prod.yml down frontend
sudo docker-compose -f docker-compose.prod.yml up -d --build frontend
```

### If Port Conflicts

```bash
# Check what's using the port
sudo lsof -i :3000
sudo lsof -i :8001

# Kill process if needed
sudo kill -9 <PID>
```

---

## 📊 Quick Status Check

```bash
# All services status
docker-compose ps

# Resource usage
docker stats --no-stream

# Recent logs
docker-compose logs --tail=50

# Specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f worker
```

---

## 🎯 Common Commands

### Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Restart service
docker-compose restart backend

# Rebuild
docker-compose up -d --build

# Stop all
docker-compose down
```

### Production

```bash
# Start
sudo docker-compose -f docker-compose.prod.yml up -d

# Stop
sudo docker-compose -f docker-compose.prod.yml down

# Rebuild
sudo docker-compose -f docker-compose.prod.yml up -d --build

# Logs
sudo docker-compose -f docker-compose.prod.yml logs -f
```

---

## 🆘 Emergency Commands

### Complete Reset (Development)

```bash
# WARNING: Deletes all data
docker-compose down -v
docker-compose up -d --build
```

### Restart Everything (Production)

```bash
sudo docker-compose -f docker-compose.prod.yml restart
```

### Clean Docker

```bash
# Remove unused resources
docker system prune -f

# Remove all stopped containers
docker container prune -f

# Remove unused images
docker image prune -a -f
```

---

## 📝 Quick Reference

| Task | Command |
|------|---------|
| Deploy docs to GitHub | `git add . && git commit -m "docs: update" && git push` |
| Deploy to server | `ssh root@server "cd /root/redditbot && git pull && docker-compose up -d --build"` |
| Check logs | `docker-compose logs -f` |
| Restart service | `docker-compose restart <service>` |
| Check status | `docker-compose ps` |
| View health | `curl http://localhost:8001/health` |

---

## 🎉 That's It!

Your documentation is updated and ready to deploy. Just run the commands above!

**Questions?** Check `DOCUMENTATION_COMPLETE.md` for full details.

---

**Last Updated:** October 10, 2025  
**Status:** Ready to deploy
