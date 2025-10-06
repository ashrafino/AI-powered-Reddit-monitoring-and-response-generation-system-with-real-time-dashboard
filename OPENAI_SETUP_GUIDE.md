# OpenAI API Setup Guide

## 🔑 Adding Your OpenAI API Key

### Step 1: Get Your API Key
1. Go to: https://platform.openai.com/account/api-keys
2. Click "Create new secret key"
3. Copy the key (starts with `sk-proj-` or `sk-`)

### Step 2: Add to .env File
Replace this line in your `.env` file:
```
OPENAI_API_KEY=your-new-openai-api-key-here
```

With your actual key:
```
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

### Step 3: Test the Configuration

#### On Local Machine:
```bash
# Test OpenAI connection
python -m app.scripts.test_openai
```

#### On Server:
```bash
# Deploy the new key
git add .env
git commit -m "Add: New OpenAI API key"
git push origin main

# On server
cd /home/deploy/apps/reddit-bot
git pull origin main
sudo docker-compose -f docker-compose.prod.yml restart backend

# Test the connection
sudo docker-compose -f docker-compose.prod.yml exec backend python -m app.scripts.test_openai
```

## ✅ Expected Results

### Success:
```
🔑 Testing OpenAI API Configuration...
API Key configured: True
API Key (first 20 chars): sk-proj-AbCdEfGhIjKl...
API Key (last 10 chars): ...XyZ1234567

🧪 Testing OpenAI API call...
Test prompt: What's the best programming language for beginners?
Generating responses...

✅ Success! Generated 2 responses:

--- Response 1 ---
Content: Python is often recommended for beginners because of its simple syntax and readability...
Score: 85
Grade: B+

--- Response 2 ---
Content: JavaScript is also a great choice since you can see immediate results in web browsers...
Score: 78
Grade: B

🎉 OpenAI API is working correctly!
```

### Failure:
```
❌ OpenAI API test failed: Incorrect API key provided
💡 The API key appears to be invalid. Please check:
   1. Key is copied correctly (no extra spaces)
   2. Key has proper permissions
   3. Account has available credits
   4. Get a new key from: https://platform.openai.com/account/api-keys
```

## 🔧 Troubleshooting

### Common Issues:

1. **Invalid API Key**
   - Double-check the key is copied correctly
   - No extra spaces or characters
   - Key starts with `sk-proj-` or `sk-`

2. **Billing Issues**
   - Check your OpenAI account has available credits
   - Add payment method if needed

3. **Rate Limits**
   - Wait a few minutes and try again
   - Check your usage limits

4. **Permissions**
   - Ensure the API key has proper permissions
   - Some keys are restricted to specific models

## 🎯 Benefits of Working OpenAI

Once configured, you'll get:
- ✅ **Smart Reddit replies** instead of "[OpenAI not configured]"
- ✅ **Quality scoring** for generated responses
- ✅ **Context-aware responses** using research data
- ✅ **Brand voice customization** for different clients
- ✅ **Multiple response options** with quality grades

## 📝 Security Notes

- ✅ **Never commit API keys to git** (use .env files)
- ✅ **Rotate keys regularly** for security
- ✅ **Monitor usage** to avoid unexpected charges
- ✅ **Set usage limits** in OpenAI dashboard

## 🚀 Next Steps

After adding your key:
1. Test locally with the script
2. Deploy to production
3. Create a configuration with scheduling
4. Run a manual scan to test AI responses
5. Check the generated responses quality

**Your Reddit bot will now generate intelligent, context-aware responses!** 🎉