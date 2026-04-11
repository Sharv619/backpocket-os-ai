# BackPocket Troubleshooting Guide

Common issues and solutions.

---

## Server & Startup Issues

### "Address already in use"
**Problem**: Port 8000 is already being used

**Solution**:
```bash
# Find and kill the process
lsof -i :8000
kill -9 <PID>

# Or use a different port
python3 -m uvicorn main:app --port 8001
```

---

### "ModuleNotFoundError: No module named 'fastapi'"
**Problem**: Dependencies not installed

**Solution**:
```bash
pip install -r requirements.txt
# Or install manually:
pip install fastapi uvicorn google-auth chromadb requests python-dotenv
```

---

### "Cannot find backpocket.db"
**Problem**: Database not initialized

**Solution**:
```bash
python3 << 'EOF'
from services.database import init_database
init_database()
print("✅ Database initialized")
EOF
```

---

## Gmail & Email Issues

### "Gmail OAuth failed" / "Invalid credentials"
**Problem**: OAuth config is wrong

**Checklist:**
- [ ] Is `GMAIL_OAUTH_JSON` in `.env` as ONE LINE (no newlines)?
- [ ] Is the JSON valid? Test with: `python3 -m json.tool <<< '{"installed":{...}}'`
- [ ] Is Gmail API enabled in Google Cloud Console?
- [ ] Did you download the credentials from the correct project?

**Solution**:
```bash
# Download fresh credentials
# 1. Google Cloud Console → Credentials → OAuth 2.0 Client ID (Desktop)
# 2. Download as JSON
# 3. Open file, copy entire contents, paste into .env as:
GMAIL_OAUTH_JSON={"installed":{...}}
# (remove all newlines, keep on one line)
```

---

### "0 unread emails" but I have emails in Gmail
**Problem**: Auth scope is wrong or connection failed

**Check these**:
1. Are emails marked as unread?
2. Is the Gmail account connected? Check `/api/gmail/unread-count`
3. Try importing manually: `python3 import_real_emails.py`

---

### Drafts showing "Error generating draft"
**Problem**: OpenRouter API failing

**Check**:
```bash
python3 test_draft.py
```

If it fails:
1. Check `OPENROUTER_API_KEY` in `.env`
2. Verify key has no typos (should start with `sk-or-v1-`)
3. Check OpenRouter account has credits
4. Try regenerating a new API key

---

## Google Sheets Issues

### "SPREADSHEET_ID is placeholder"
**Problem**: You haven't configured your actual Google Sheet

**Solution**:
1. Open your Google Sheet in browser
2. Copy ID from URL: `https://docs.google.com/spreadsheets/d/` **[THIS PART]** `/edit`
3. Paste into `.env`: `SPREADSHEET_ID=YOUR_ID_HERE`
4. Restart server

---

### "Service account doesn't have access"
**Problem**: You didn't share the sheet with the service account email

**Solution**:
1. Open `credentials.json` file
2. Find `"client_email"` field (looks like `backpocket-test@project.iam.gserviceaccount.com`)
3. Copy that email
4. Open your Google Sheet
5. Click **Share** → Paste email → Grant **Editor** access

---

### "Sheets API not enabled"
**Problem**: You forgot to enable it in Google Cloud

**Solution**:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Search for "Google Sheets API"
3. Click it → **Enable**

---

## Database Issues

### "Database is locked"
**Problem**: SQLite is being accessed by multiple processes

**Solution**:
```bash
# Kill all Python processes
pkill -f python3

# Or be specific:
pkill -f "uvicorn.*main"

# Restart server
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 &
```

---

### "Column does not exist"
**Problem**: Database schema is outdated

**Solution**:
```bash
# Backup existing database
cp backpocket.db backpocket.db.backup

# Delete and reinitialize
rm backpocket.db
python3 << 'EOF'
from services.database import init_database
init_database()
print("✅ Database reinitialized")
EOF

# Re-import data
python3 import_real_emails.py
```

---

## API & Integration Issues

### "openrouter/auto model not found"
**Problem**: Using wrong model name

**Solution**: In `services/gemini.py` and `services/agentic_rag.py`, model should be:
```
"model": "openrouter/auto"
```

Not `mistralai/mistral-7b-instruct:free` (that model is deprecated).

---

### "Ollama connection refused"
**Problem**: Ollama server isn't running

**Solution**:
```bash
# Check if running
curl http://localhost:11434/api/health

# If not, start it
ollama serve

# If you don't have Ollama, that's fine
# BackPocket will fall back to OpenRouter/Gemini
```

---

### "WHAPI token invalid"
**Problem**: Token is wrong or expired

**Solution**:
1. Go to [WHAPI.cloud](https://whapi.cloud/)
2. Check your account
3. Generate new API token
4. Update in `.env`

---

## Frontend/Dashboard Issues

### "Blank page on http://127.0.0.1:8000"
**Problem**: Server is running but serving empty page

**Try**:
```bash
# Check if server is responding
curl http://127.0.0.1:8000/api/health

# Check if static files are being served
curl http://127.0.0.1:8000/static/index.html
```

If getting 404, check that `static/` folder exists with `index.html` in it.

---

### "New nav sections (AGENTIC RAG, BLOG, DRIVE) not showing"
**Problem**: JavaScript toggle functions not loaded

**Solution**: 
Clear browser cache (Ctrl+Shift+Delete) and reload page.

---

### "Sidebar looks broken/misaligned"
**Problem**: CSS not loaded properly

**Solution**:
1. Hard refresh: `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac)
2. Open DevTools (F12) → Console → check for errors
3. Check that CSS is being served: Open DevTools → Network → filter "css"

---

## Performance Issues

### "Dashboard is slow/laggy"
**Problem**: Too much data loaded or JavaScript not optimized

**Try**:
1. Close other browser tabs
2. Disable browser extensions
3. Check browser console (F12) for JavaScript errors
4. Limit query results in API calls

For bulk data, try pagination:
```
GET /api/emails?limit=20&offset=0
```

---

### "Emails take forever to import"
**Problem**: Trying to import too many at once

**Solution**:
```bash
# Import in batches
# Edit import_real_emails.py to limit results:
# emails = get_unread_emails(limit=50)  # Start with 50
```

---

## AI/LLM Issues

### "Drafts are poor quality"
**Problem**: AI model selection or prompt issue

**Check**:
1. Is OpenRouter working? Run `python3 test_openrouter.py`
2. Are you on the right model? Should be `openrouter/auto`
3. Check that context is being loaded: Look for `learned_patterns` in logs

---

### "Learned patterns not being applied"
**Problem**: Corrections not being saved or retrieved

**Check**:
1. When you correct a draft, is it saving to `corrections` table?
2. Are patterns being retrieved? Look in logs: `get_learned_patterns()`
3. Try manually checking database:
```bash
sqlite3 backpocket.db "SELECT * FROM corrections LIMIT 5;"
```

---

## Common Error Messages

### "ValueError: invalid literal for int()"
**Usually**: Tier or ID field is malformed
**Fix**: Check that tier is 1-5 (integer), IDs are strings

---

### "JSONDecodeError"
**Usually**: API response isn't valid JSON
**Fix**: Check that OpenRouter/Gemini API keys are correct

---

### "Connection refused: (Errno 111)"
**Usually**: Can't reach external API
**Fix**: Check internet connection, API endpoint URL, firewall

---

### "TypeError: 'NoneType' object is not subscriptable"
**Usually**: Trying to access field on None value
**Fix**: Check that API returned expected data structure

---

## Getting Help

### Check Logs
```bash
# See server output while running
# Look for ERROR or WARNING lines
```

### Enable Debug Mode
```bash
# In main.py, add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Individual Components
```bash
# Test Gmail
python3 << 'EOF'
from services.gmail import get_gmail_service
svc = get_gmail_service()
print("✅ Gmail service OK" if svc else "❌ Gmail service failed")
EOF

# Test OpenRouter
python3 test_openrouter.py

# Test database
python3 << 'EOF'
import services.database as db
conn = db.sqlite3.connect(db.DB_PATH)
print("✅ Database OK")
EOF
```

---

## Still Stuck?

1. **Check .env file** - Missing or wrong API keys?
2. **Check logs** - What's the actual error message?
3. **Try restarting** - Kill and restart the server
4. **Check internet** - Are external APIs accessible?
5. **See [API_KEYS.md](./API_KEYS.md)** - API setup might be incomplete

---

## Report an Issue

When reporting a problem, include:
- Error message (full text)
- What you were doing when it happened
- Server logs (output of running command)
- Your Python version: `python3 --version`
- Your OS (Windows/Mac/Linux)

This helps us debug faster!
