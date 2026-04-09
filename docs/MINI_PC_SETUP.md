# BackPocket OS - Mini-PC Setup Guide

## Overview
This guide covers setting up BackPocket OS on a mini-pc for 24/7 operation.

---

## Prerequisites

### Hardware
- Mini-pc (e.g., Intel NUC, Raspberry Pi 4, or old laptop)
- Internet connection (24/7)
- Power (24/7)

### Software
- Windows 10/11
- Python 3.10+
- Google Drive (for syncing code)

---

## Step 1: Install Python

1. Download Python from https://python.org
2. **IMPORTANT:** Check "Add Python to PATH"
3. Verify: `python --version`

---

## Step 2: Install Ollama (Local AI)

1. Go to https://ollama.com
2. Download for Windows
3. Install
4. Test: `ollama run llama3.2`
5. Exit: `/bye`

**Why Ollama?**
- Free AI (no Gemini costs)
- Data stays local (privacy)
- Works 24/7 without internet for AI

---

## Step 3: Sync Code via Google Drive

1. Install Google Drive desktop app
2. Sign in: cherry@bigbossgroup.com.au
3. Your folder: `BackPocket System/08 Ai Agent and Automations/BackPocket OS`

**Or use Git:**
```bash
cd C:\BackPocket_MVP
git clone <your-repo-url>
git pull  # To update
```

---

## Step 4: Install Python Dependencies

```cmd
cd C:\BackPocket_MVP
pip install -r requirements.txt
```

---

## Step 5: Configure Environment

1. Copy `.env` file (ask Cherry for credentials)
2. Or create new with your API keys:
   - GEMINI_API_KEY
   - SPREADSHEET_ID
   - WHAPI_TOKEN
   - FOUNDER_PHONE

---

## Step 6: Setup Auto-Start (24/7)

1. Run `SETUP_AUTOSTART.bat` as Administrator
2. Server will start automatically when Windows boots

**Manual start:**
```cmd
LAUNCH_BACKPOCKET_TWIN.bat
```

---

## Accessing the Dashboard

- Local: http://localhost:8000/dashboard
- Network: http://<mini-pc-ip>:8000/dashboard

---

## Troubleshooting

### Server Not Starting
```cmd
python -c "import main"
```
Check for errors

### Check Logs
```cmd
type backpocket.log
```

### Restart Server
```cmd
RESTART_SERVER.bat
```

---

## Costs

| Component | Cost |
|-----------|------|
| Server (Mini-pc) | ~$20/month power |
| Ollama (Local AI) | FREE |
| Gemini API (Cloud) | ~$0.01/email |
| WhatsApp | ~$0.005/message |
| Gmail/Sheets | FREE |

**Recommendation:** Use Ollama for all AI to reduce costs

---

## For Developers

### Update Code
1. Make changes on desktop
2. Save to Google Drive
3. On mini-pc: Google Drive auto-syncs
4. Restart server

### Add New Features
1. Test on desktop first
2. Commit to git (if using)
3. Push changes
4. Pull on mini-pc
5. Restart

---

## Support

- Check logs: `/api/status`
- View pending: `/api/pending`
- View corrections: `/api/corrections`
- View instructions: `/api/sender-instructions`
