# Quick Setup Guide

## First Time Setup

After deploying the application, follow these steps:

### 1. Login as Admin
- Go to http://your-server-ip:3000
- Login with:
  - Email: `admin@example.com`
  - Password: `admin123`
- **⚠️ Change this password immediately after first login!**

### 2. Create a Client
- Click "Clients" in the top navigation
- Enter a client name (e.g., "My Company", "Acme Corp")
- Click "Create Client"
- Note the Client ID that appears

### 3. Create a Configuration
- Click "Configs" in the top navigation
- Select your client from the dropdown (or it will auto-select if you're logged in as a client user)
- Fill in:
  - **Subreddits to Monitor**: Comma-separated list (e.g., `technology,programming,webdev`)
  - **Keywords to Track**: Comma-separated list (e.g., `API,integration,automation`)
  - **Reddit Username** (optional): Filter posts by specific user
  - **Scan Interval**: How often to check Reddit (default: 6 hours)
  - **Active Hours**: Time range when scanning should occur
  - **Active Days**: Days of the week to scan
- Check "Configuration Active"
- Click "Create Configuration"

### 4. Run Your First Scan
- Go to "Dashboard"
- Click "Scan Now" button
- Wait 30-60 seconds for results
- New posts will appear with AI-generated responses

### 5. Review and Use Responses
- Click on any post to expand it
- Review the AI-generated responses
- Each response shows:
  - Quality score (0-100)
  - Grade (A-F)
  - Quality feedback
- Click "Edit" to modify a response
- Click "Copy" to copy to clipboard
- Paste into Reddit!

## Automation

The system automatically scans based on your configuration:
- **Default**: Every 6 hours
- **Customizable**: Set your own interval, hours, and days
- **Background**: Runs via Celery worker
- **Real-time**: New posts appear automatically

## Troubleshooting

### "No clients found" error
1. Go to /clients page
2. Create a client
3. Go back to /configs and try again

### "Scan Now" doesn't work
1. Check if Celery worker is running:
   ```bash
   docker-compose ps
   ```
2. Check logs:
   ```bash
   docker-compose logs celery_worker --tail=50
   ```

### No new posts appearing
1. Verify your configuration is active
2. Check if keywords match posts in those subreddits
3. Try broader keywords
4. Check Reddit API credentials in .env file

### Response editing doesn't save
1. Check browser console for errors
2. Verify backend is running
3. Check authentication token is valid

## API Credentials

Make sure these are set in your `.env` file:

```env
# Reddit API
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=RedditAnalyzer/1.0

# OpenAI (for AI responses)
OPENAI_API_KEY=your_openai_key

# Optional: Enhanced context
SERPAPI_API_KEY=your_serpapi_key
YOUTUBE_API_KEY=your_youtube_key
```

## Security

### Change Default Password
```bash
# SSH into server
ssh root@your-server-ip

# Access backend container
docker-compose exec backend python

# In Python shell:
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()
admin = db.query(User).filter(User.email == "admin@example.com").first()
admin.hashed_password = get_password_hash("your_new_secure_password")
db.commit()
print("Password updated!")
```

### Update Secret Key
Edit `.env` file and change:
```env
SECRET_KEY=your_very_long_random_secret_key_here
```

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review FIXES_IMPLEMENTED.md for recent changes
3. Check GitHub issues

## Features Implemented

✅ Client management page
✅ Automatic default client creation
✅ Filter bar expanded by default
✅ Subreddit guidelines compliance (automatic)
✅ Response editing (fixed)
✅ 6-hour default scan interval
✅ Real-time scanning
✅ Quality scoring for responses
✅ Copy to clipboard functionality
