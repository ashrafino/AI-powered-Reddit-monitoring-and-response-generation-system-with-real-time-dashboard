# 🚀 Quick Deployment Guide

## What Was Fixed
- ✅ Added missing `anyio` import in `app/api/routers/ops.py`
- ✅ Added missing `generate_reddit_replies_with_research` import
- ✅ Scan feature now works correctly

## Deploy to Server (3 Commands)

### Option 1: Automated (Recommended)
```bash
ssh root@your-server-ip
cd /root/reddit-bot
git pull && bash DEPLOY_TO_SERVER.sh
```

### Option 2: Manual (5 Commands)
```bash
ssh root@your-server-ip
cd /root/reddit-bot
git pull origin main
source .venv/bin/activate
sudo systemctl restart reddit-bot-backend
```

## Verify Deployment

```bash
# Check service status
sudo systemctl status reddit-bot-backend

# View logs
sudo journalctl -u reddit-bot-backend -n 50

# Test scan endpoint
curl -X POST http://localhost:8000/api/ops/scan \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Test via Browser

1. Go to your app: `https://your-domain.com`
2. Login as admin
3. Go to "Configs" page
4. Create a config with "Auto-scan" enabled
5. ✅ Should see "Scan started in background"

## Rollback (If Needed)

```bash
cd /root/reddit-bot
git reset --hard HEAD~2
sudo systemctl restart reddit-bot-backend
```

## Files Changed
- `app/api/routers/ops.py` (2 lines added)

## No Breaking Changes
- ✅ No database migrations needed
- ✅ No config changes needed
- ✅ No dependency updates needed
- ✅ Backward compatible

## Support
See `SERVER_DEPLOYMENT_COMMANDS.md` for detailed instructions.
