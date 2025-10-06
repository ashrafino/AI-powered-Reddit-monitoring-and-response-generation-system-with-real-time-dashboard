# OpenAI API Fix + Scheduling Features

## 🎯 Issues Fixed

### 1. ✅ OpenAI API Error
**Problem:** Invalid API key causing 401 errors
**Solution:** 
- Commented out invalid API key in `.env`
- System gracefully handles missing OpenAI key
- Shows "[OpenAI not configured]" responses instead of crashing
- Added instructions to get new key

### 2. ✅ Scheduling Features Added
**Problem:** No way to specify when to scrape
**Solution:** Added comprehensive scheduling options:
- **Scan Interval:** 5 min, 15 min, 30 min, 1 hour, 3 hours, 6 hours, 12 hours, daily
- **Active Hours:** Start/end time (e.g., 9 AM to 6 PM)
- **Active Days:** Select which days of the week to scan

## 📦 Files Changed

### Backend
- `app/models/config.py` - Added scheduling columns
- `app/schemas/config.py` - Added scheduling fields to API
- `app/api/routers/configs.py` - Handle scheduling in create/update
- `app/scripts/create_db_migration.py` - NEW: Add columns to existing DB
- `.env` - Commented out invalid OpenAI key

### Frontend
- `frontend/pages/configs.tsx` - Added scheduling UI controls

## 🚀 Deployment Steps

### Step 1: Push Changes (Local)
```bash
git add app/models/config.py \
  app/schemas/config.py \
  app/api/routers/configs.py \
  app/scripts/create_db_migration.py \
  frontend/pages/configs.tsx \
  .env \
  OPENAI_AND_SCHEDULING_FIX.md

git commit -m "Fix: OpenAI API error + Add scheduling features for scraping"
git push origin main
```

### Step 2: Deploy Backend (Server)
```bash
cd /home/deploy/apps/reddit-bot
git pull origin main

# Add scheduling columns to database
sudo docker-compose -f docker-compose.prod.yml exec backend python -m app.scripts.create_db_migration

# Rebuild and restart backend
sudo docker-compose -f docker-compose.prod.yml build backend --no-cache
sudo docker-compose -f docker-compose.prod.yml up -d backend
```

### Step 3: Deploy Frontend (Server)
```bash
sudo docker-compose -f docker-compose.prod.yml build frontend --no-cache
sudo docker-compose -f docker-compose.prod.yml up -d frontend
```

## ✅ New Features

### Scheduling Options:
1. **Scan Interval**
   - Every 5 minutes (default)
   - Every 15 minutes
   - Every 30 minutes
   - Every hour
   - Every 3 hours
   - Every 6 hours
   - Every 12 hours
   - Daily

2. **Active Hours**
   - Set start time (e.g., 09:00)
   - Set end time (e.g., 18:00)
   - Only scans during these hours

3. **Active Days**
   - Select specific days of the week
   - Mon, Tue, Wed, Thu, Fri, Sat, Sun
   - Default: All days active

### OpenAI Handling:
- ✅ No crashes when API key is invalid
- ✅ Graceful fallback responses
- ✅ Clear "[OpenAI not configured]" messages
- ✅ Instructions to get new API key

## 🎨 New UI

### Configuration Form Now Includes:
```
Subreddits to Monitor: [technology, programming]
Keywords to Track: [API, automation]

┌─ Scan Interval ─┐ ┌─── Active Hours ───┐ ┌─── Active Days ───┐
│ Every 5 minutes │ │ 09:00 to 18:00    │ │ [Mon][Tue][Wed]   │
└─────────────────┘ └───────────────────┘ │ [Thu][Fri] Sat Sun │
                                          └───────────────────┘

[✓] Configuration Active        [Create Configuration]
```

## 🔧 Technical Details

### Database Schema:
```sql
ALTER TABLE client_configs ADD COLUMN scan_interval_minutes INTEGER DEFAULT 5;
ALTER TABLE client_configs ADD COLUMN scan_start_hour INTEGER DEFAULT 0;
ALTER TABLE client_configs ADD COLUMN scan_end_hour INTEGER DEFAULT 23;
ALTER TABLE client_configs ADD COLUMN scan_days VARCHAR(20) DEFAULT '1,2,3,4,5,6,7';
```

### API Payload:
```json
{
  "client_id": 1,
  "reddit_subreddits": ["technology", "programming"],
  "keywords": ["API", "automation"],
  "scan_interval_minutes": 30,
  "scan_start_hour": 9,
  "scan_end_hour": 18,
  "scan_days": "1,2,3,4,5",
  "is_active": true
}
```

## 🎉 Benefits

### For Users:
- ✅ **Control when scraping happens** (business hours only)
- ✅ **Adjust frequency** (don't overwhelm Reddit API)
- ✅ **Weekend scheduling** (pause on weekends if needed)
- ✅ **No OpenAI crashes** (system works without valid key)

### For System:
- ✅ **Reduced API calls** (configurable intervals)
- ✅ **Better resource management** (time-based controls)
- ✅ **Graceful degradation** (works without OpenAI)
- ✅ **User-friendly scheduling** (visual day selector)

## 🔮 Future Enhancements

Could add:
- Timezone support
- Holiday scheduling
- Rate limiting per subreddit
- Custom OpenAI model selection
- Bulk schedule templates

## 📝 Usage Examples

### Business Hours Only:
- Interval: Every 15 minutes
- Hours: 09:00 to 17:00
- Days: Mon-Fri

### Light Monitoring:
- Interval: Every 3 hours
- Hours: 00:00 to 23:00
- Days: All days

### Weekend Focus:
- Interval: Every 30 minutes
- Hours: 10:00 to 22:00
- Days: Sat, Sun

**Deploy and enjoy the new scheduling features!** 🚀