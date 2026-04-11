# BackPocket - Quick Start (5 Minutes)

Get up and running with BackPocket in just 5 minutes.

---

## Prerequisites
- Python 3.8+
- Google Account
- Internet connection

---

## Step 1: Install (1 minute)

```bash
cd /home/lade/Hackathons/.git/backpocket-mvp
pip install -r requirements.txt
```

---

## Step 2: Configure (2 minutes)

### Get Gmail OAuth JSON
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project → Enable Gmail API
3. Create OAuth 2.0 credentials (Desktop)
4. Download JSON
5. Copy entire JSON to `.env`:
   ```
   GMAIL_OAUTH_JSON={"installed":{...entire json...}}
   ```

### Get API Keys
1. OpenRouter: [https://openrouter.ai/](https://openrouter.ai/) → API Keys → Copy key
   ```
   OPENROUTER_API_KEY=sk-or-v1-...
   ```

2. Google Gemini: [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
   ```
   GEMINI_API_KEY=AIzaSy...
   ```

3. (Optional) Google Sheets ID: Get from your Sheet URL
   ```
   SPREADSHEET_ID=1hD7FxWj...
   ```

---

## Step 3: Initialize Database (30 seconds)

```bash
python3 << 'EOF'
from services.database import init_database
init_database()
print("✅ Ready to go!")
EOF
```

---

## Step 4: Start Server (30 seconds)

```bash
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

## Step 5: Open Dashboard

Open your browser:
```
http://127.0.0.1:8000/static/index.html
```

---

## That's It! 🎉

You now have:
- ✅ Email automation with AI drafts
- ✅ 3 specialized AI twins (Accountant, Auditor, Admin)
- ✅ Document analysis with vision
- ✅ Google Drive integration
- ✅ Blog generation with AI
- ✅ 4-5 step workflows for construction/tradies

---

## Next Steps

### Optional: Import Real Emails
```bash
python3 import_real_emails.py
```

This fetches your actual Gmail messages and populates the dashboard.

### Optional: Add More Services
- **WhatsApp**: Add `WHAPI_TOKEN` and `FOUNDER_PHONE` to .env
- **Text-to-Speech**: Add `ELEVENLABS_API_KEY` to .env
- **Local AI**: Install Ollama and add `OLLAMA_BASE_URL` to .env

---

## Documentation

| Page | Purpose |
|------|---------|
| [README.md](./README.md) | Overview & features |
| [SETUP.md](./SETUP.md) | Full installation guide |
| [WORKFLOWS.md](./WORKFLOWS.md) | 4-5 step business workflows |
| [SPECIALIZED_WORKFLOWS.md](./SPECIALIZED_WORKFLOWS.md) | Construction-specific AI prompts |
| [API_KEYS.md](./API_KEYS.md) | All API key setup |
| [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) | Fix common issues |

---

## Common Commands

```bash
# Start server
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000

# Import real emails
python3 import_real_emails.py

# Test draft generation
python3 test_draft.py

# Test OpenRouter API
python3 test_openrouter.py

# View logs in real-time
tail -f server.log
```

---

## Troubleshooting

**Getting "Address already in use"?**
```bash
pkill -f "uvicorn.*8000"
```

**Getting "ModuleNotFoundError"?**
```bash
pip install -r requirements.txt
```

**Getting "SPREADSHEET_ID is placeholder"?**
Go to your Google Sheet, copy ID from URL, add to `.env`.

More help: See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

---

## Questions?

- 📖 See full docs in this folder
- 🔧 Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- 🚀 Jump to [WORKFLOWS.md](./WORKFLOWS.md) to see what's possible

---

**You're all set! Start exploring the dashboard.** 🚀
