# Deployment Instructions for UX Improvements

## 📋 Pre-Deployment Checklist

Before deploying, ensure:
- [ ] Backend is running: `pm2 status`
- [ ] Frontend is running: `pm2 status`
- [ ] You have a backup of current code
- [ ] OpenAI API key has access to fine-tuned model

---

## 🚀 Deployment Steps

### Step 1: Verify Changes
```bash
# Check what files were modified
git status

# Review the changes
git diff app/services/openai_service.py
git diff frontend/pages/dashboard.tsx
git diff frontend/components/ResponseManager.tsx
git diff frontend/components/SearchAndFilter.tsx
git diff frontend/pages/configs.tsx
```

### Step 2: Test Backend Changes Locally (Optional)
```bash
# The OpenAI model change doesn't require restart
# But you can test it:
cd app
python -c "from services.openai_service import generate_reddit_replies; print('OK')"
```

### Step 3: Build Frontend
```bash
cd frontend
npm run build
```

**Expected output:**
```
✓ Compiled successfully
✓ Collecting page data
✓ Generating static pages
✓ Finalizing page optimization
```

### Step 4: Restart Services
```bash
# Restart backend (optional, but recommended)
pm2 restart reddit-bot-backend

# Restart frontend
pm2 restart reddit-bot-frontend

# Check status
pm2 status
```

**Expected output:**
```
┌─────┬──────────────────────┬─────────┬─────────┐
│ id  │ name                 │ status  │ restart │
├─────┼──────────────────────┼─────────┼─────────┤
│ 0   │ reddit-bot-backend   │ online  │ 1       │
│ 1   │ reddit-bot-frontend  │ online  │ 1       │
└─────┴──────────────────────┴─────────┴─────────┘
```

### Step 5: Verify Deployment
```bash
# Check backend logs
pm2 logs reddit-bot-backend --lines 50

# Check frontend logs
pm2 logs reddit-bot-frontend --lines 50

# Look for any errors
pm2 logs --err
```

---

## ✅ Post-Deployment Testing

### Test 1: Fine-Tuned Model
1. Go to Dashboard
2. Click "Scan Now" (or wait for automatic scan)
3. Check that responses are generated
4. Verify responses sound natural (not generic)

**Expected:** Responses should be more brand-aligned and natural

### Test 2: Post Dates
1. Go to Dashboard
2. Look at any post card
3. Verify date appears next to subreddit name

**Expected:** "Dec 10, 2025 02:30 PM" format

### Test 3: Collapsed Responses
1. Go to Dashboard
2. Find a post with responses
3. Verify responses are collapsed by default
4. Click to expand
5. Click again to collapse

**Expected:** Responses start collapsed, show preview text

### Test 4: Client Filter
1. Go to Dashboard
2. Click "Filters" button
3. Look for "Client" dropdown
4. Select a client
5. Click "Apply Filters"

**Expected:** Only posts for that client show

### Test 5: Auto-Scan
1. Go to Configs page
2. Create a new configuration
3. Verify "Auto-scan after creating" is checked
4. Click "Create Configuration"
5. Wait for success message

**Expected:** "Configuration created successfully! Scan started in background."

### Test 6: Scan Button Feedback
1. Go to Dashboard
2. Click "Scan Now"
3. Watch for loading spinner
4. Check status message appears

**Expected:** Button shows "Scanning..." with spinner

---

## 🐛 Troubleshooting

### Issue: OpenAI Model Not Found Error

**Symptoms:**
```
Error: The model 'ft:gpt-4o-mini-2024-07-18:180-marketing:wellbefore-reddit:CCgr05CY' does not exist
```

**Solution:**
1. Verify your OpenAI API key has access to the fine-tuned model
2. Check the model ID is correct in your OpenAI dashboard
3. Ensure the fine-tuned model is still active
4. If needed, update the model ID in `app/services/openai_service.py`

### Issue: Frontend Not Updating

**Symptoms:**
- Changes not visible in browser
- Old UI still showing

**Solution:**
```bash
# Clear Next.js cache
cd frontend
rm -rf .next
npm run build
pm2 restart reddit-bot-frontend

# Clear browser cache
# Or open in incognito mode
```

### Issue: Responses Not Collapsing

**Symptoms:**
- All responses expanded by default
- No collapse toggle

**Solution:**
```bash
# Verify the build completed
cd frontend
npm run build

# Check for TypeScript errors
npm run type-check

# Restart frontend
pm2 restart reddit-bot-frontend
```

### Issue: Client Filter Not Showing

**Symptoms:**
- No "Client" dropdown in filters

**Solution:**
1. Verify you have multiple clients in database
2. Check browser console for errors
3. Verify API endpoint `/api/clients` is working:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/clients
   ```

### Issue: Scan Button Not Working

**Symptoms:**
- Button doesn't respond
- No loading state

**Solution:**
```bash
# Check backend is running
pm2 status

# Check backend logs
pm2 logs reddit-bot-backend

# Verify you have active configs
# Check database or use API:
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/configs
```

---

## 🔄 Rollback Plan

If something goes wrong:

### Quick Rollback
```bash
# Revert code changes
git checkout HEAD -- app/services/openai_service.py
git checkout HEAD -- frontend/

# Rebuild frontend
cd frontend
npm run build

# Restart services
pm2 restart all
```

### Full Rollback
```bash
# Revert to previous commit
git log --oneline  # Find previous commit hash
git reset --hard PREVIOUS_COMMIT_HASH

# Rebuild and restart
cd frontend
npm run build
pm2 restart all
```

---

## 📊 Monitoring

### Check Application Health
```bash
# View all logs
pm2 logs

# View specific service
pm2 logs reddit-bot-backend
pm2 logs reddit-bot-frontend

# Monitor in real-time
pm2 monit

# Check memory/CPU usage
pm2 status
```

### Check for Errors
```bash
# Backend errors
pm2 logs reddit-bot-backend --err

# Frontend errors  
pm2 logs reddit-bot-frontend --err

# All errors
pm2 logs --err
```

---

## 📈 Success Metrics

After deployment, monitor:

1. **Response Quality**
   - Check AI scores are reasonable (60-90 range)
   - Verify responses sound natural
   - No generic "AI-sounding" language

2. **User Experience**
   - Responses load collapsed
   - Filters work smoothly
   - Scan button provides feedback
   - Post dates display correctly

3. **Performance**
   - Scan completes in reasonable time (30-60 seconds)
   - No memory leaks
   - No excessive CPU usage

4. **Error Rate**
   - No OpenAI API errors
   - No frontend console errors
   - No backend exceptions

---

## 🎯 Expected Behavior After Deployment

### Dashboard
- ✅ Post dates visible next to subreddit
- ✅ Responses collapsed by default
- ✅ Client filter in filters panel
- ✅ Scan button shows loading state
- ✅ Better error messages

### Configs
- ✅ Auto-scan checkbox visible
- ✅ Auto-scan enabled by default
- ✅ Scan triggers after config creation

### AI Responses
- ✅ More natural, less generic
- ✅ Better brand alignment
- ✅ Improved quality scores

---

## 📞 Support

If you encounter issues:

1. **Check logs first:**
   ```bash
   pm2 logs --lines 100
   ```

2. **Verify services are running:**
   ```bash
   pm2 status
   ```

3. **Check environment variables:**
   ```bash
   cat .env | grep -E "OPENAI|REDDIT"
   ```

4. **Test API endpoints:**
   ```bash
   # Health check
   curl http://localhost:8000/api/health
   
   # Test OpenAI
   curl -X POST http://localhost:8000/api/ops/scan \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

---

## ✨ Deployment Complete!

Once all tests pass, your deployment is complete. Users should now experience:

- 🎯 Better AI responses with fine-tuned model
- 📅 Visible post dates
- 📦 Collapsed responses for cleaner UI
- 🔍 Client filtering capability
- ⚡ Auto-scan on config creation
- 💬 Better feedback and error messages

Enjoy the improved experience! 🚀
