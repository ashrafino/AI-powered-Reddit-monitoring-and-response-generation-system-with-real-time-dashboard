# 🎯 Pre-Deployment Preparation Guide

## Complete this BEFORE starting deployment

### ✅ Checklist: Things to Prepare

---

## 1. API Keys & Credentials

### Reddit API
**Get it from**: https://www.reddit.com/prefs/apps

**Steps**:
1. Go to Reddit preferences
2. Click "apps" tab
3. Click "create app" or "create another app"
4. Fill in:
   - Name: `Reddit Bot`
   - Type: Select "script"
   - Description: `Reddit monitoring bot`
   - About URL: Leave blank
   - Redirect URI: `http://localhost:8080`
5. Click "create app"
6. **Save these**:
   ```
   REDDIT_CLIENT_ID: _________________ (under app name)
   REDDIT_CLIENT_SECRET: _________________ (secret field)
   ```

---

### OpenAI API
**Get it from**: https://platform.openai.com/api-keys

**Steps**:
1. Create OpenAI account
2. Add payment method (required)
3. Go to API keys section
4. Click "Create new secret key"
5. Name it: `Reddit Bot Production`
6. **Save this** (shown only once):
   ```
   OPENAI_API_KEY: sk-proj-_________________ 
   ```

**Cost**: ~$10-50/month depending on usage

---

### SerpAPI (Google Search)
**Get it from**: https://serpapi.com/

**Steps**:
1. Sign up for account
2. Choose plan:
   - Free: 100 searches/month
   - Paid: $50/month for 5,000 searches
3. Go to dashboard
4. Copy API key
5. **Save this**:
   ```
   SERPAPI_API_KEY: _________________
   ```

---

### YouTube API
**Get it from**: https://console.cloud.google.com/

**Steps**:
1. Create Google Cloud account
2. Create new project: `Reddit Bot`
3. Enable YouTube Data API v3
4. Go to Credentials
5. Create API key
6. Restrict key to YouTube Data API v3
7. **Save this**:
   ```
   YOUTUBE_API_KEY: _________________
   ```

**Cost**: Free (10,000 requests/day)

---

## 2. Domain Name (Optional but Recommended)

### Purchase Domain
**Recommended registrars**:
- Namecheap: https://www.namecheap.com
- Google Domains: https://domains.google
- GoDaddy: https://www.godaddy.com

**Cost**: $10-15/year

**Save this**:
```
Domain: _________________
Registrar: _________________
Login: _________________
```

---

## 3. DigitalOcean Account

### Create Account
**Sign up**: https://www.digitalocean.com

**Steps**:
1. Create account
2. Verify email
3. Add payment method
4. Get $200 credit (if using referral link)

**Save this**:
```
Email: _________________
Password: _________________ (use password manager)
```

---

## 4. SSH Key Pair

### Generate SSH Key (if you don't have one)

**On Mac/Linux**:
```bash
# Generate key
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"

# Press Enter for default location (~/.ssh/id_rsa)
# Enter passphrase (optional but recommended)

# View public key
cat ~/.ssh/id_rsa.pub
```

**On Windows**:
```powershell
# Use Git Bash or WSL
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"
```

**Save this**:
```
SSH Key Location: ~/.ssh/id_rsa
Public Key: (copy from cat ~/.ssh/id_rsa.pub)
```

---

## 5. Email Configuration (Optional)

### Gmail App Password
**For email notifications**

**Steps**:
1. Enable 2FA on Gmail
2. Go to: https://myaccount.google.com/apppasswords
3. Create app password for "Mail"
4. **Save this**:
   ```
   SMTP_USER: your-email@gmail.com
   SMTP_PASSWORD: _________________ (16-char app password)
   ```

---

## 6. Monitoring (Optional)

### Sentry
**For error tracking**

**Get it from**: https://sentry.io

**Steps**:
1. Create account (free tier available)
2. Create new project
3. Choose "FastAPI"
4. Copy DSN
5. **Save this**:
   ```
   SENTRY_DSN: _________________
   ```

---

## 7. GitHub Repository (Recommended)

### Create Repository
**Steps**:
1. Go to GitHub
2. Create new repository
3. Name it: `reddit-bot`
4. Make it private
5. Push your code:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin git@github.com:USERNAME/reddit-bot.git
   git push -u origin main
   ```

**Save this**:
```
Repository URL: _________________
```

---

## 8. Password Generation

### Generate Secure Passwords

**Run these commands**:
```bash
# SECRET_KEY
openssl rand -hex 32

# POSTGRES_PASSWORD
openssl rand -base64 32

# REDIS_PASSWORD
openssl rand -base64 32

# ADMIN_PASSWORD (or create your own)
openssl rand -base64 16
```

**Save these**:
```
SECRET_KEY: _________________
POSTGRES_PASSWORD: _________________
REDIS_PASSWORD: _________________
ADMIN_PASSWORD: _________________
```

---

## 9. Admin User

### Decide Admin Credentials

**Save these**:
```
ADMIN_EMAIL: _________________
ADMIN_PASSWORD: _________________ (from above or custom)
```

---

## 10. Budget Planning

### Monthly Cost Estimate

```
DigitalOcean Droplet:
  - Basic (2GB): $12/month
  - Standard (4GB): $24/month
  
Domain Name: $1-2/month ($10-15/year)

API Costs:
  - OpenAI: $10-50/month (usage-based)
  - SerpAPI: $0-50/month (free tier or paid)
  - YouTube: $0 (free)
  
Total: $25-125/month
```

**Budget approved**: ☐ Yes ☐ No

---

## 11. Documentation Template

### Create a secure document with all credentials

**Template**:
```
# Reddit Bot Production Credentials
Date: _________________
Deployed by: _________________

## Server
Droplet IP: _________________
SSH User: deploy
SSH Key: ~/.ssh/id_rsa

## Domain
Domain: _________________
Registrar: _________________

## Application
Admin Email: _________________
Admin Password: _________________
Frontend URL: https://_________________

## Database
Postgres Password: _________________
Redis Password: _________________

## API Keys
Reddit Client ID: _________________
Reddit Client Secret: _________________
OpenAI API Key: _________________
SerpAPI Key: _________________
YouTube API Key: _________________

## Email (Optional)
SMTP User: _________________
SMTP Password: _________________

## Monitoring (Optional)
Sentry DSN: _________________

## Security
SECRET_KEY: _________________

## Notes
_________________
_________________
```

**Save this document securely** (password manager, encrypted file, etc.)

---

## 12. Pre-Flight Checklist

Before starting deployment, verify:

- [ ] All API keys obtained and tested
- [ ] Domain purchased (if using)
- [ ] DigitalOcean account created
- [ ] Payment method added
- [ ] SSH key generated
- [ ] Passwords generated
- [ ] Credentials documented securely
- [ ] Budget approved
- [ ] Code committed to Git
- [ ] Team notified
- [ ] Backup plan ready
- [ ] Support contacts documented

---

## 13. Test API Keys Locally

### Verify keys work before deployment

```bash
# Test Reddit API
python -c "
import praw
reddit = praw.Reddit(
    client_id='YOUR_CLIENT_ID',
    client_secret='YOUR_CLIENT_SECRET',
    user_agent='test'
)
print('Reddit API:', 'OK' if reddit.read_only else 'FAIL')
"

# Test OpenAI API
python -c "
import openai
openai.api_key = 'YOUR_OPENAI_KEY'
try:
    openai.models.list()
    print('OpenAI API: OK')
except:
    print('OpenAI API: FAIL')
"
```

---

## 14. Deployment Day Checklist

**On deployment day**:

- [ ] All credentials ready
- [ ] Time allocated (2-3 hours)
- [ ] Backup internet connection available
- [ ] Team available for support
- [ ] Rollback plan ready
- [ ] Monitoring tools ready
- [ ] Documentation open
- [ ] Coffee ready ☕

---

## 15. Emergency Contacts

**Save these**:
```
DigitalOcean Support: https://cloud.digitalocean.com/support
OpenAI Support: https://help.openai.com
Reddit API Support: https://www.reddit.com/r/redditdev

Team Lead: _________________
DevOps: _________________
On-call: _________________
```

---

## ✅ Ready to Deploy?

If you've completed all items above, you're ready!

**Next steps**:
1. Open `DIGITALOCEAN_DEPLOYMENT_GUIDE.md`
2. Follow `DEPLOYMENT_CHECKLIST.md`
3. Reference `QUICK_DEPLOY_REFERENCE.md`
4. Deploy! 🚀

---

**Estimated prep time**: 1-2 hours
**Estimated deployment time**: 1-2 hours
**Total time**: 2-4 hours

Good luck! 🍀
