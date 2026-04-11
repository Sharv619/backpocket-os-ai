# BackPocket OS - Quick Start Guide

## Server Status
- **URL:** http://127.0.0.1:8000
- **Dashboard:** http://127.0.0.1:8000/dashboard
- **Version:** 2.2

## To Start Server

```bash
cd /path/to/backpocket-mvp
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
```

## To Stop Server
```bash
pkill -f "uvicorn main:app"
```

---

## Required Setup (For Full Functionality)

### 1. Gmail Credentials
Create `gmail_credentials.json` with your OAuth credentials.

### 2. Environment Variables
Create `.env` file:
```
GOOGLE_APPLICATION_CREDENTIALS=credentials.json
SPREADSHEET_ID=your_sheet_id
GEMINI_API_KEY=your_key
WHAPI_TOKEN=your_token
FOUNDER_PHONE=your_phone
```

---

## Current State (Without Credentials)

| Feature | Status |
|---------|--------|
| Server | ✅ Running |
| Dashboard | ✅ Works |
| Pending Emails | ✅ 5 mock emails |
| Gmail API | ❌ Needs credentials |
| Sheets API | ❌ Needs credentials |
| Gemini AI | ❌ Needs API key |
| WhatsApp | ❌ Needs token |

---

## Mock Data Included

The system comes with 5 sample pending emails for demo:
- Tier 1: Client email (Priority)
- Tier 2: ATO (Government)
- Tier 3: Telstra (Supplier)
- Tier 4: Suitedash Digest (Updates)
- Tier 5: Spam

---

## Ollama (Optional - Local AI)

Already installed on system. Available models:
- `llama3.2:1b` - Small, fast
- `codegemma:2b` - Code assistance
- `all-minilm:l6-v2` - Embeddings
- `nomic-embed-text` - Text embeddings

To use Ollama instead of Gemini:
```bash
# Set in .env
OLLAMA_BASE_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3.2:1b
```

---

*For full setup guide, see `docs/04_SETUP/SETUP_GUIDE.md`*