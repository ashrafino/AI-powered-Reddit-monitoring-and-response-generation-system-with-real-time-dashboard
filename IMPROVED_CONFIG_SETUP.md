# ✅ Your App Already Has 24/7 Automatic Scanning!

## Current Status

Your Reddit bot is **already configured** to scan automatically every 5 minutes! 🎉

### What's Running:

1. **Celery Beat** (Scheduler) - Running ✅
   - Scans Reddit every 5 minutes
   - Updates metrics daily
   - Generates trends weekly
   - Cleans up old data weekly

2. **Celery Worker** - Running ✅
   - Processes scan tasks
   - Generates AI responses
   - Handles background jobs

3. **Backend API** - Running ✅
4. **Frontend** - Running ✅
5. **Database** - Running ✅
6. **Redis** - Running ✅

## How to Verify It's Working

### 1. Check Celery Beat Logs
```bash
sudo docker-compose -f docker-compose.prod.yml logs -f beat
```

You should see messages like:
```
Scheduler: Sending due task scan-reddit-every-5-min
```

### 2. Check Worker Logs
```bash
sudo docker-compose -f docker-compose.prod.yml logs -f worker
```

You should see:
```
Task app.tasks.reddit_tasks.scan_reddit received
Starting Reddit scan
Found X new matches
```

### 3. Check Dashboard
- Go to: http://146.190.50.85
- Login with: admin@example.com / admin123
- Wait 5 minutes
- Refresh the page
- You should see new posts appearing automatically!

## Configuration Management

### Current Configs (Already Created)
You have 5 active configurations scanning:

1. **General Q&A** - AskReddit, explainlikeimfive, NoStupidQuestions
2. **Programming** - learnprogramming, webdev, javascript, python
3. **Fitness** - fitness, loseit, bodyweightfitness
4. **Finance** - personalfinance, investing, financialindependence
5. **Tech** - technology, gadgets, android, apple

### To Manage Configs:
1. Go to: http://146.190.50.85/configs
2. You can:
   - ✅ Add new configurations
   - ✅ Edit existing ones
   - ✅ Toggle Active/Inactive
   - ✅ Delete configurations

## Customization Options

### Change Scan Frequency

Edit `app/celery_app.py` and change the schedule:

```python
"scan-reddit-every-5-min": {
    "task": "app.tasks.reddit_tasks.scan_reddit",
    "schedule": 300.0,  # Change this number (in seconds)
},
```

Options:
- Every 1 minute: `60.0`
- Every 5 minutes: `300.0` (current)
- Every 10 minutes: `600.0`
- Every 30 minutes: `1800.0`
- Every hour: `3600.0`

Then rebuild:
```bash
cd ~/apps/reddit-bot
git pull
sudo docker-compose -f docker-compose.prod.yml up -d --build beat
```

### Add More Subreddits/Keywords

**Option 1: Via Web UI** (Easiest)
1. Go to http://146.190.50.85/configs
2. Click "Edit" on any configuration
3. Add more subreddits or keywords (comma-separated)
4. Click "Update"
5. Done! Next scan will use new settings

**Option 2: Via API**
```bash
curl -X PUT http://146.190.50.85/api/configs/1 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reddit_subreddits": "AskReddit,technology,programming",
    "keywords": "how to,tutorial,help,question"
  }'
```

### Create New Configuration

1. Go to: http://146.190.50.85/configs
2. Fill in:
   - **Client ID**: 1 (or your client ID)
   - **Subreddits**: `gaming,pcgaming,buildapc` (comma-separated)
   - **Keywords**: `build,recommend,help,advice` (comma-separated)
   - **Active**: ✓ Checked
3. Click "Create"
4. Done! It will start scanning in the next cycle (within 5 minutes)

## Monitoring

### Check Scan Activity
```bash
# View all logs
sudo docker-compose -f docker-compose.prod.yml logs -f

# View only scan activity
sudo docker-compose -f docker-compose.prod.yml logs -f worker | grep "scan"

# View last 100 lines
sudo docker-compose -f docker-compose.prod.yml logs --tail=100 worker
```

### Check Database for New Posts
```bash
# Count posts
sudo docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d redditbot -c "SELECT COUNT(*) FROM matched_posts;"

# See recent posts
sudo docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d redditbot -c "SELECT id, title, subreddit, created_at FROM matched_posts ORDER BY created_at DESC LIMIT 10;"
```

## Troubleshooting

### Scans Not Running?

1. **Check if Beat is running:**
```bash
sudo docker-compose -f docker-compose.prod.yml ps beat
```

2. **Check Beat logs:**
```bash
sudo docker-compose -f docker-compose.prod.yml logs beat
```

3. **Restart Beat:**
```bash
sudo docker-compose -f docker-compose.prod.yml restart beat
```

### No New Posts Found?

This is normal if:
- Your keywords are very specific
- Subreddits have low activity
- Posts were already scanned before

**Solutions:**
- Add more subreddits
- Add more general keywords
- Wait longer (some subreddits post infrequently)
- Check larger subreddits like AskReddit

### Worker Not Processing?

1. **Check worker status:**
```bash
sudo docker-compose -f docker-compose.prod.yml ps worker
```

2. **Check worker logs:**
```bash
sudo docker-compose -f docker-compose.prod.yml logs worker
```

3. **Restart worker:**
```bash
sudo docker-compose -f docker-compose.prod.yml restart worker
```

## Performance Tips

### For High-Volume Scanning:

1. **Increase worker concurrency** (in `docker-compose.prod.yml`):
```yaml
worker:
  command: celery -A app.celery_app.celery_app worker --loglevel=INFO --concurrency=4
```

2. **Add more workers:**
```bash
sudo docker-compose -f docker-compose.prod.yml up -d --scale worker=3
```

3. **Upgrade droplet** if needed:
- Current: 2GB RAM
- Recommended for heavy use: 4GB RAM ($24/month)

## Summary

✅ **Automatic scanning is ALREADY WORKING!**
- Scans every 5 minutes
- Processes all active configurations
- Generates AI responses
- Stores in database
- Updates dashboard

✅ **You can customize:**
- Scan frequency (edit celery_app.py)
- Subreddits (via /configs page)
- Keywords (via /configs page)
- Active/Inactive status (via /configs page)

✅ **Monitor via:**
- Dashboard: http://146.190.50.85
- Logs: `docker-compose logs -f`
- Database queries

**Your bot is running 24/7 and scanning automatically!** 🚀

Just wait 5-10 minutes and check the dashboard - you should see new posts appearing!
