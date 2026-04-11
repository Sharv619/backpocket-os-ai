# API Keys & Services Configuration Guide

Complete reference for setting up all external services BackPocket integrates with.

---

## 🔑 Critical Keys (Required)

### 1. OpenRouter API Key
**Purpose**: LLM calls for drafts, blog generation, and AI analysis  
**Cost**: Pay-per-use (~$0.001-$0.01 per request)  
**Setup Time**: 2 minutes

**Get it:**
1. Go to [OpenRouter.ai](https://openrouter.ai/)
2. Sign up with email
3. Go to **API Keys** in dashboard
4. Click **Create Key**
5. Copy the key (starts with `sk-or-v1-`)

**Add to .env:**
```env
OPENROUTER_API_KEY=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
```

**Verify it works:**
```bash
curl -X POST https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer sk-or-v1-..." \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openrouter/auto",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

Should return a response (not 401 Unauthorized).

---

### 2. Gmail OAuth Configuration
**Purpose**: Read/send emails, authenticate user  
**Cost**: Free (part of Google Cloud)  
**Setup Time**: 5-10 minutes

**Get it:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project called "BackPocket"
3. Enable **Gmail API**
4. Go to **Credentials** → **Create OAuth 2.0 Client ID**
5. Choose **Desktop application**
6. Download JSON file
7. Copy entire JSON (remove newlines) into .env

**Add to .env:**
```env
GMAIL_OAUTH_JSON={"installed":{"client_id":"...","project_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_secret":"...","redirect_uris":["http://localhost:8080"]}}
```

**Note**: The JSON must be on ONE LINE (no newlines).

---

### 3. Google Sheets API
**Purpose**: Read/write to your business spreadsheet  
**Cost**: Free (part of Google Cloud)  
**Setup Time**: 5 minutes

**Get it:**
1. In Google Cloud Console, enable **Google Sheets API**
2. Create a **Service Account**:
   - Go to Credentials
   - Create Service Account
   - Create JSON key
   - Download and save as `credentials.json`

**Add to .env:**
```env
GOOGLE_APPLICATION_CREDENTIALS=credentials.json
SPREADSHEET_ID=1hD7FxWj7X0NzKk...  # From your Sheet URL
```

**Get your Sheet ID:**
- Open your Google Sheet in browser
- Copy from URL: `https://docs.google.com/spreadsheets/d/**1hD7FxWj7X0NzKk.../edit`

**Important**: Share the spreadsheet with your service account email (found in credentials.json).

---

### 4. Google Drive API
**Purpose**: Sync files from Drive into RAG system  
**Cost**: Free (part of Google Cloud)  
**Setup Time**: 2 minutes (reuses Sheets setup)

**Enable it:**
1. In Google Cloud Console, enable **Google Drive API**
2. Already have credentials from Sheets setup

**Add to .env:**
```env
# Reuse GOOGLE_APPLICATION_CREDENTIALS from above
```

---

## 📚 Backup/Secondary Keys (Recommended)

### 5. Google Gemini API Key
**Purpose**: Backup LLM model (if OpenRouter is down)  
**Cost**: Free tier available  
**Setup Time**: 2 minutes

**Get it:**
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click **Create API Key**
3. Copy the key

**Add to .env:**
```env
GEMINI_API_KEY=AIzaSyCkmHFYUB5kSgbbHZoptUoTCoGyI9B2iio
```

**Note**: Free tier is rate-limited (~10 requests/day). BackPocket intelligently falls back to this when OpenRouter is unavailable.

---

### 6. ElevenLabs API Key (Optional)
**Purpose**: Text-to-speech for voice outputs  
**Cost**: Free tier available (~10,000 characters/month)  
**Setup Time**: 2 minutes

**Get it:**
1. Go to [ElevenLabs.io](https://elevenlabs.io/)
2. Sign up
3. Go to **API Keys**
4. Copy your key

**Add to .env:**
```env
ELEVENLABS_API_KEY=sk_c301b1d1ec405bd7321666508ac03956331424a459640882
```

---

## 🤖 Local AI (Optional, but Recommended)

### 7. Ollama (Free, Local, No API Key)
**Purpose**: Free local LLM for privacy + speed  
**Cost**: Free  
**Setup Time**: 10 minutes

**Install:**
```bash
# macOS
brew install ollama

# Linux
curl https://ollama.ai/install.sh | sh

# Windows/WSL2
Download from https://ollama.ai
```

**Run:**
```bash
ollama serve
# Runs on http://localhost:11434
```

**Add to .env:**
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=moondream
```

**Benefits:**
- ✅ Free (runs locally)
- ✅ No API calls = faster
- ✅ Privacy (data never leaves your machine)
- ✅ No rate limits

---

## 📱 WhatsApp/SMS (Optional)

### 8. WHAPI Token
**Purpose**: Send WhatsApp/SMS notifications  
**Cost**: Pay-per-message (~$0.01-0.05 each)  
**Setup Time**: 5 minutes

**Get it:**
1. Go to [WHAPI.cloud](https://whapi.cloud/)
2. Sign up
3. Go to **API Token** in dashboard
4. Copy token

**Add to .env:**
```env
WHAPI_TOKEN=your_whapi_token_here
FOUNDER_PHONE=+61412345678
```

**Test it:**
```bash
curl -X POST https://whapi.cloud/api/send \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+61412345678",
    "text": "Test message"
  }'
```

---

## 🎬 Video/Streaming (Optional)

### 9. Google YouTube API (Optional)
**Purpose**: Auto-upload videos to YouTube  
**Cost**: Free API  
**Setup Time**: 10 minutes

**Enable it:**
1. Google Cloud Console → Enable **YouTube Data API v3**
2. Create OAuth 2.0 key (same as Gmail)
3. Store in .env

Not currently used in BackPocket, but available for future expansion.

---

## 🔐 Security Best Practices

### DO ✅
- Store all keys in `.env` file
- Never commit `.env` to git
- Rotate keys monthly
- Use service accounts for APIs (not personal accounts)
- Use restricted scopes (only needed permissions)

### DON'T ❌
- Store keys in code
- Share keys in emails/Slack
- Use same key for multiple services
- Commit `credentials.json` to git

### .gitignore
Make sure `.env` and `credentials.json` are ignored:
```bash
# .gitignore
.env
.env.local
.env.*.local
credentials.json
*.pem
*.key
```

---

## 🧪 Testing API Keys

### Test All Keys at Once
```bash
python3 << 'EOF'
import os
from dotenv import load_dotenv

load_dotenv()

checks = {
    "OpenRouter": os.getenv("OPENROUTER_API_KEY"),
    "Gemini": os.getenv("GEMINI_API_KEY"),
    "Gmail OAuth": os.getenv("GMAIL_OAUTH_JSON"),
    "Spreadsheet ID": os.getenv("SPREADSHEET_ID"),
    "ElevenLabs": os.getenv("ELEVENLABS_API_KEY"),
    "WHAPI Token": os.getenv("WHAPI_TOKEN"),
    "Ollama URL": os.getenv("OLLAMA_BASE_URL"),
}

for service, key in checks.items():
    status = "✅" if key and key != "your_..." else "❌"
    print(f"{status} {service}: {'Set' if key and key != 'your_...' else 'MISSING'}")
EOF
```

### Test OpenRouter Specifically
```bash
# Save as test_openrouter.py
python3 << 'EOF'
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("❌ OPENROUTER_API_KEY not set")
    exit(1)

try:
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "backpocket.ai"
        },
        json={
            "model": "openrouter/auto",
            "messages": [{"role": "user", "content": "Say 'working'"}],
            "max_tokens": 10
        },
        timeout=10
    )
    
    if response.status_code == 200:
        print("✅ OpenRouter is working!")
        print(f"Response: {response.json()}")
    else:
        print(f"❌ OpenRouter error: {response.status_code}")
        print(f"Details: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")
EOF
```

---

## 💰 Cost Estimation

Rough monthly costs (assuming active use):

| Service | Cost | Notes |
|---------|------|-------|
| **OpenRouter** | $10-50 | ~1000 drafts/month at $0.01-0.05 each |
| **Google APIs** | $0 | Free tier sufficient for < 100k requests/day |
| **Gmail** | $0 | Built into Google account |
| **WHAPI** | $5-20 | 50-200 messages/month |
| **ElevenLabs** | $0-5 | Free tier usually sufficient |
| **Ollama** | $0 | Local, no cost |
| **Total** | **$15-75/month** | Scales with usage |

---

## Troubleshooting

### "401 Unauthorized" on OpenRouter
- Check that API key doesn't have typos
- Key should start with `sk-or-v1-`
- Try creating a new key and replace old one

### "Gmail OAuth failed"
- Check that JSON is on ONE line (no newlines)
- Verify OAuth consent screen is configured
- Try re-downloading credentials.json

### "Spreadsheet not found"
- Check SPREADSHEET_ID is correct (from URL)
- Verify service account email has access to sheet
- Share sheet with: `backpocket-test@project.iam.gserviceaccount.com`

### "Ollama not responding"
- Check that Ollama is running: `ollama serve`
- Verify URL is correct: `http://localhost:11434`
- Pull a model: `ollama pull moondream`

---

## Next Steps

1. **Get critical keys** (OpenRouter, Gmail, Sheets)
2. **Test each key** using the test scripts above
3. **Add to .env** and restart server
4. **Enable optional services** as needed (WHAPI, ElevenLabs)
5. **Run import script** to test everything works

See [SETUP.md](./SETUP.md) for full installation guide.
