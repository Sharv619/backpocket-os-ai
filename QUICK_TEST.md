# BackPocket OS - Quick Test Guide

## TL;DR - Start Testing in 2 Minutes

### 1. Run Diagnostic Check

```bash
python3 scripts/diagnostic_check.py
```

Expected output: `4/4 checks passed ✓`

### 2. Start the Server

```bash
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Watching for file changes in [directory]
```

### 3. Open Dashboard

In browser: http://127.0.0.1:8000/static/index.html

You should see 5 demo emails (DEMO-00001 through DEMO-00005) with:
- Sender emails
- Tier labels (1-5)
- AI-generated drafts
- Status indicators

---

## Quick Test Commands (in another terminal)

### Test 1: Health Check

```bash
curl http://127.0.0.1:8000/health
# Expected: {"status": "ok", ...}
```

### Test 2: Get All Pending Approvals

```bash
curl -s http://127.0.0.1:8000/api/pending | jq .
# Expected: Array of 5 objects with ref_id, sender, subject, tier, draft_body
```

### Test 3: Count Pending

```bash
curl -s http://127.0.0.1:8000/api/pending | jq 'length'
# Expected: 5
```

### Test 4: Approve an Email

```bash
curl -X POST http://127.0.0.1:8000/api/approve \
  -H "Content-Type: application/json" \
  -d '{"ref_id": "DEMO-00001"}'
```

Then verify count decreased:

```bash
curl -s http://127.0.0.1:8000/api/pending | jq 'length'
# Expected: 4 (was 5)
```

### Test 5: Get Drafts

```bash
curl -s http://127.0.0.1:8000/api/drafts | jq .
```

### Test 6: Document Upload

```bash
# Create a test file
echo "Test invoice content" > test.txt

# Upload
curl -X POST http://127.0.0.1:8000/api/documents/upload \
  -F "file=@test.txt" \
  -F "document_type=invoice"

# Expected: JSON with document_id, filename, status: "uploaded"
```

### Test 7: Twin Chat

```bash
curl -X POST http://127.0.0.1:8000/api/twin-chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How many tier 1 emails do I have?",
    "conversation_id": "test"
  }'

# Expected: AI response analyzing pending approvals
```

---

## Gmail Integration Setup (Optional)

To enable real Gmail syncing:

### Step 1: Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credential (type: Desktop Application)
5. Download as JSON
6. Save to project root as `gmail_credentials.json`

### Step 2: Update .env

Add to `.env`:
```
GOOGLE_APPLICATION_CREDENTIALS=gmail_credentials.json
SPREADSHEET_ID=your-sheet-id-if-using-sheets
```

### Step 3: First Run

When you call `/api/pending` for the first time:
1. Browser opens asking for Gmail permission
2. Click "Allow"
3. `token.json` is created automatically
4. Future calls fetch real Gmail inbox

### Test Gmail Integration

```bash
# This will trigger OAuth if not authorized yet
curl http://127.0.0.1:8000/api/pending

# Then search for specific emails
curl -X POST http://127.0.0.1:8000/api/search-gmail \
  -H "Content-Type: application/json" \
  -d '{"q": "from:your-email@gmail.com"}'
```

---

## Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| `Connection refused` | Make sure server is running on port 8000 |
| `Database is locked` | Kill existing Python processes, restart |
| `ModuleNotFoundError` | Install: `pip install -r requirements.txt` |
| `Gmail credentials not found` | Download from Google Cloud Console, save as `gmail_credentials.json` |
| `Gemini API not working` | Check `.env` has valid `GEMINI_API_KEY` |
| `404 on /static/index.html` | Server must be running, try `http://127.0.0.1:8000/static/index.html` |

---

## Pipeline Status

| Pipeline | Status | Notes |
|----------|--------|-------|
| Pending Approvals | ✓ Working | 5 demo emails loaded |
| Email Triage | ✓ Working | Gemini API (needs key for real processing) |
| Approval & History | ✓ Working | Database tracking approvals |
| Draft Management | ✓ Working | Save, retrieve, modify drafts |
| Document Analysis | ✓ Working | Needs Ollama for vision AI |
| Gmail Sync | ✓ Optional | Requires OAuth setup |
| Twin Brain Chat | ✓ Working | Conversational AI interface |

---

## Performance Checklist

After starting the server, verify these response times:

```bash
# Should all complete in < 2 seconds

time curl -s http://127.0.0.1:8000/api/pending > /dev/null
time curl -s http://127.0.0.1:8000/api/drafts > /dev/null
time curl -s http://127.0.0.1:8000/health > /dev/null
```

---

## For Full Details

See `TEST_PIPELINES.md` for comprehensive testing guide including:
- All API endpoints
- Document analysis with Ollama
- Email searching
- Conversation management
- Mobile API endpoints
- Troubleshooting guide

---

## Support Files

| File | Purpose |
|------|---------|
| `.env.example` | Template for environment variables |
| `AGENTS.md` | Quick reference for services and gotchas |
| `TEST_PIPELINES.md` | Comprehensive testing guide |
| `scripts/diagnostic_check.py` | Automated system check |
| `scripts/demo_seed.py` | Reset/populate demo data |

---

## Next: Gmail Credentials

The project is ready to test! To enable real Gmail integration:

1. Get free credentials: https://console.cloud.google.com
2. Download JSON file
3. Save as `gmail_credentials.json` in project root
4. Update `.env` with `GOOGLE_APPLICATION_CREDENTIALS=gmail_credentials.json`
5. Restart server and test `/api/pending` endpoint

All real Gmail emails will now flow through the system and be processed.
