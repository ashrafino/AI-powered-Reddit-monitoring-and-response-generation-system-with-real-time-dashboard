# Quick Fixes Reference

## What Was Fixed

### 1. ✅ Add New Client
- **Location:** New "Clients" menu item (admin only)
- **Action:** Click "Clients" → Enter name → "Create Client"

### 2. ✅ Filter Bar Expanded
- **Location:** Dashboard page
- **Change:** Filter bar now shows expanded by default

### 3. ✅ Compliance Ack Removed + AI Compliance
- **Removed:** "Compliance Ack" button
- **Added:** Automatic subreddit rules in AI prompts
- **Benefit:** AI responses now follow subreddit guidelines automatically

### 4. ✅ Response Editing Fixed
- **Location:** Response cards on dashboard
- **Action:** Click "Edit" → Modify text → "Save"
- **Status:** Now works correctly

### 5. ✅ Default Scan Interval = 6 Hours
- **Location:** Configs page
- **Change:** New configs default to 6 hours (360 minutes)
- **Note:** Existing configs keep their current settings

### 6. ⚠️ Automation Check Needed
**If posts are 4 days old, Celery may not be running:**

```bash
# Check if running
ps aux | grep celery

# Start Celery worker
celery -A app.celery_app worker --loglevel=info &

# Start Celery beat (scheduler)
celery -A app.celery_app beat --loglevel=info &
```

### 7. ⚠️ Scan Now Button
**Should work if Celery is running. If not:**
- Check browser console for errors
- Check backend logs
- Ensure Celery worker is running (see #6)

---

## How to Apply Changes

1. **Restart backend:**
   ```bash
   # Stop current backend process
   # Then restart:
   python -m uvicorn app.main:app --reload
   ```

2. **Restart Celery (if running):**
   ```bash
   # Stop existing Celery processes
   pkill -f celery
   
   # Start worker
   celery -A app.celery_app worker --loglevel=info &
   
   # Start beat scheduler
   celery -A app.celery_app beat --loglevel=info &
   ```

3. **Rebuild frontend (if needed):**
   ```bash
   cd frontend
   npm run build
   ```

---

## Quick Test

1. ✅ Go to /clients → Create a client
2. ✅ Go to /dashboard → Verify filters are expanded
3. ✅ Edit a response → Verify it saves
4. ✅ Create new config → Verify default is 6 hours
5. ⚠️ Click "Scan Now" → Check if new posts appear
6. ⚠️ Wait for next scheduled scan → Verify automation works

---

## Troubleshooting

**Scan Now doesn't work:**
- Check if Celery worker is running
- Check backend logs for errors
- Try manual scan from terminal: `celery -A app.celery_app call app.tasks.reddit_tasks.scan_reddit`

**No new posts after 6 hours:**
- Verify Celery beat is running
- Check celery_worker.log for scan execution
- Verify configs are marked as "active"
- Check Reddit API credentials in .env

**Response edit doesn't save:**
- Check browser console for errors
- Verify backend is running
- Check authentication token is valid
