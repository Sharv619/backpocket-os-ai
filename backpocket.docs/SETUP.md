# BackPocket OS - Installation & Setup Guide

Complete step-by-step guide to get BackPocket running on your system.

---

## Prerequisites

- **Python**: 3.8 or higher
- **System**: Linux, macOS, or Windows with WSL2
- **Internet**: For Google Cloud APIs and OpenRouter
- **Git**: For version control (optional but recommended)

### Optional (for advanced features)
- **Ollama**: For local AI (improves speed and privacy)
- **ChromaDB**: Vector database (included with setup)

---

## 1. Clone & Install

### Step 1.1: Clone the Repository
```bash
cd /home/lade/Hackathons/.git/backpocket-mvp
```

Or clone if you don't have it:
```bash
git clone https://github.com/your-repo/backpocket-mvp.git
cd backpocket-mvp
```

### Step 1.2: Create Virtual Environment (Recommended)
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 1.3: Install Dependencies
```bash
pip install -r requirements.txt
```

Key packages:
- `fastapi` - Web framework
- `google-auth` - Google Cloud authentication
- `chromadb` - Vector database
- `requests` - HTTP client
- `python-dotenv` - Environment variables

---

## 2. Google Cloud Setup

### Step 2.1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project called "BackPocket"
3. Enable these APIs:
   - Gmail API
   - Google Sheets API
   - Google Drive API
   - Google Vision API (optional, for document processing)

### Step 2.2: Create OAuth 2.0 Credentials
1. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
2. Choose **Desktop application**
3. Download the JSON file
4. Copy the entire JSON and paste it into your `.env` file as `GMAIL_OAUTH_JSON`

Example `.env`:
```
GMAIL_OAUTH_JSON={"installed": {"client_id": "...", ...}}
```

### Step 2.3: Set Up Service Account (Optional, for Sheets/Drive)
1. Go to **Credentials** → **Service Account**
2. Create a new service account
3. Download JSON credentials
4. Share your Google Sheet with the service account email
5. Set `GOOGLE_APPLICATION_CREDENTIALS=credentials.json`

---

## 3. API Keys Configuration

### OpenRouter (for AI drafts and blog generation)
1. Sign up at [OpenRouter.ai](https://openrouter.ai/)
2. Go to **API Keys** and create a new key
3. Add to `.env`:
```
OPENROUTER_API_KEY=sk-or-v1-...
```

### Google Gemini (backup AI model)
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Add to `.env`:
```
GEMINI_API_KEY=AIzaSy...
```

### WhatsApp/WHAPI (Optional, for notifications)
1. Sign up at [WHAPI.cloud](https://whapi.cloud/)
2. Get your API token
3. Add to `.env`:
```
WHAPI_TOKEN=your_token_here
FOUNDER_PHONE=+1234567890
```

### ElevenLabs (Optional, for voice/speech)
1. Sign up at [ElevenLabs](https://elevenlabs.io/)
2. Get API key
3. Add to `.env`:
```
ELEVENLABS_API_KEY=sk_...
```

---

## 4. Configure .env File

Copy the template and fill in your values:

```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

**Critical variables:**
```env
# Google APIs
GMAIL_OAUTH_JSON={"installed":{...}}
SPREADSHEET_ID=1hD7FxWj7...  # Your Google Sheet ID
GOOGLE_APPLICATION_CREDENTIALS=credentials.json

# AI APIs
OPENROUTER_API_KEY=sk-or-v1-...
GEMINI_API_KEY=AIzaSy...

# Local AI (Optional)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=moondream

# WhatsApp (Optional)
WHAPI_TOKEN=your_token_here
FOUNDER_PHONE=+61...

# Demo Mode (set to 1 for safe testing)
DEMO_MODE=1

# Business Info
BUSINESS_NAME=Your Web Accountant
BUSINESS_EMAIL=hello@example.com
```

---

## 5. Get Your Google Sheet ID

Your sheet data is critical. BackPocket needs your actual Google Sheet ID:

1. Open your Google Sheet in browser
2. Copy the ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/1hD7FxWj7X0NzKk.../edit
                                      ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑
                                      This is your Sheet ID
   ```
3. Paste into `.env`:
   ```
   SPREADSHEET_ID=1hD7FxWj7X0NzKk...
   ```
4. **Important**: Share the sheet with your service account email (from credentials.json)

---

## 6. Initialize Database

BackPocket uses SQLite (included). Initialize it:

```bash
python3 << 'EOF'
from services.database import init_database
init_database()
print("✅ Database initialized")
EOF
```

This creates:
- `backpocket.db` (main database)
- 22+ tables for emails, clients, instructions, etc.

---

## 7. Import Real Emails (Optional)

Populate your dashboard with actual Gmail data:

```bash
python3 import_real_emails.py
```

This:
- Fetches unread emails from your Gmail
- Classifies by tier (client/internal/spam)
- Generates AI drafts for review
- Stores in database

**Note**: This respects DEMO_MODE. Set `DEMO_MODE=0` to actually send emails.

---

## 8. (Optional) Set Up Ollama for Local AI

For faster, cheaper, and more private AI:

### Install Ollama
```bash
# macOS
brew install ollama

# Linux
curl https://ollama.ai/install.sh | sh

# Windows/WSL2
Download from https://ollama.ai
```

### Run Ollama
```bash
ollama serve
# Runs on http://localhost:11434
```

### Pull a Model
```bash
ollama pull moondream  # For vision
ollama pull mistral    # For text generation
```

### Configure in BackPocket
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=moondream
```

---

## 9. Start the Server

### Development Mode
```bash
python3 -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Flags:
- `--reload` - Auto-reload on code changes
- `--host 127.0.0.1` - Listen only locally (secure)
- `--port 8000` - Use port 8000

### Production Mode
```bash
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Access the Dashboard
Open your browser:
```
http://127.0.0.1:8000/static/index.html
```

---

## 10. Verify Everything Works

### Check Server Health
```bash
curl http://127.0.0.1:8000/api/health
```

Should return: `{"status":"healthy"}`

### Test Gmail Connection
```bash
curl http://127.0.0.1:8000/api/gmail/unread-count
```

Should return the number of unread emails.

### Test Draft Generation
```bash
curl -X POST http://127.0.0.1:8000/api/draft \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Invoice",
    "sender": "bills@example.com",
    "snippet": "Please find attached invoice"
  }'
```

Should generate a professional response.

---

## Troubleshooting Setup

### Issue: "SPREADSHEET_ID is placeholder"
**Solution**: Get your actual Google Sheet ID and add it to `.env`

### Issue: "Gmail OAuth failed"
**Solution**: Check that `GMAIL_OAUTH_JSON` in `.env` is valid JSON

### Issue: "OpenRouter API errors"
**Solution**: Check that `OPENROUTER_API_KEY` is valid and has credits

### Issue: "Address already in use"
**Solution**: Another process is using port 8000. Kill it:
```bash
pkill -f "uvicorn.*8000"
# Or use a different port: --port 8001
```

### Issue: "Database locked"
**Solution**: SQLite is in use. Restart the server:
```bash
pkill -f "python3.*main"
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 &
```

---

## Next Steps

Once setup is complete:

1. **Import Real Data**: Run `import_real_emails.py`
2. **Explore Features**: Try each section in the dashboard
3. **Configure Sheets**: Add your actual Google Sheet ID
4. **Read Documentation**: See [README.md](./README.md) for feature guides
5. **Customize**: Update business info in `.env`

---

## Getting Help

Check these resources:
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Common issues
- [API_KEYS.md](./API_KEYS.md) - Detailed API setup
- [ARCHITECTURE.md](./ARCHITECTURE.md) - How the system works

Or check the main project README for community support.
