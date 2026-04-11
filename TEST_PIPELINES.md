# BackPocket OS - Pipeline Testing Guide

## Environment Status

### Verified Components ✓

- **Python Environment**: 3.x with all major dependencies installed
- **Database**: `backpocket.db` (SQLite) with 22 tables
- **Demo Data**: 5 sample emails pre-seeded in `pending_approvals` table
- **Application**: `main.py` imports successfully
- **Framework**: FastAPI + Uvicorn ready

### Google APIs Available ✓

- `google-api-python-client` ✓
- `google-auth-oauthlib` ✓
- `google-auth` ✓
- `google-genai` (for Gemini) ✓

---

## Quick Start (Local Testing)

### 1. Start the Application

```bash
cd /home/lade/Hackathons/.git/backpocket-mvp
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Expected output:
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 2. Access the Dashboard

Open in browser:
```
http://127.0.0.1:8000/static/index.html
```

The dashboard should show:
- 5 pending approvals (DEMO-00001 to DEMO-00005)
- Tier labels for each (Tier 1-5)
- Preview snippets from the email subjects
- Age of each message

---

## Core Pipeline Tests

### Pipeline 1: Get Pending Approvals

**Purpose**: Fetch all pending emails awaiting approval/response

**Test Command**:
```bash
curl -s http://127.0.0.1:8000/api/pending | jq .
```

**Expected Response**:
- HTTP 200 OK
- Array of 5+ approval objects with fields:
  - `ref_id`: Unique identifier (e.g., "DEMO-00001")
  - `sender`: Email address
  - `subject`: Email subject
  - `tier`: Priority tier (1-5)
  - `draft_body`: AI-generated response draft
  - `status`: "pending" or "approved"
  - `timestamp`: Creation time

**What it tests**:
- Database connectivity
- API routing
- Response formatting

---

### Pipeline 2: Email Triage (Gemini AI)

**Purpose**: Automatically classify and draft responses for emails

**Requirements**:
- `.env` file with `GEMINI_API_KEY=<your-key>`
- Setup: Get key from [Google AI Studio](https://aistudio.google.com/app/apikey)

**How it works**:
1. User submits email to system
2. Gemini API classifies tier (1=urgent, 5=spam)
3. Gemini generates response draft
4. Draft saved to database
5. User can approve or revise

**Test in UI**:
1. Open Dashboard → Click "Upload Email" or use incoming Gmail
2. Check dashboard for new item with AI-generated draft
3. Review draft quality and tier classification

**Test via API**:
```bash
# Example: Process a new email (requires proper payload)
curl -X POST http://127.0.0.1:8000/api/pending \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "test@example.com",
    "subject": "Test Email",
    "body": "This is a test message"
  }'
```

**Known Issues to Watch For**:
- If Gemini key missing: responses will be generic fallback
- If API rate limit hit: "quota exceeded" error (wait 1 minute)
- Draft quality varies with email clarity

---

### Pipeline 3: Approval & Response

**Purpose**: Approve AI draft and track response sent

**Test Commands**:

```bash
# Approve an item (mark as approved)
curl -X POST http://127.0.0.1:8000/api/approve \
  -H "Content-Type: application/json" \
  -d '{"ref_id": "DEMO-00001"}'
```

**Expected Response**:
- HTTP 200 OK
- Status changes from "pending" → "approved"
- Item removed from pending queue
- Moved to action history

**Verify**:
```bash
curl -s http://127.0.0.1:8000/api/pending | jq 'length'
# Should now return 4 (was 5)
```

---

### Pipeline 4: Draft Management

**Purpose**: Save, revise, and track draft responses

**Test Commands**:

**Save a new draft**:
```bash
curl -X POST http://127.0.0.1:8000/api/save-draft \
  -H "Content-Type: application/json" \
  -d '{
    "ref_id": "DEMO-00002",
    "draft_body": "Hi Mike,\n\nThank you for your message. I will review and respond shortly.\n\nBest regards, Steve"
  }'
```

**Get all drafts**:
```bash
curl -s http://127.0.0.1:8000/api/drafts | jq .
```

**Get specific draft**:
```bash
curl -s http://127.0.0.1:8000/api/draft/DEMO-00001 | jq .
```

**Expected Response Fields**:
- `ref_id`: Identifier
- `draft_body`: Full response text
- `updated_at`: Last modified timestamp
- `status`: "draft", "pending_review", or "sent"

---

### Pipeline 5: Document Analysis

**Purpose**: Upload and analyze documents with vision AI (Moondream/Ollama)

**Prerequisites**:
- Ollama running locally: `ollama serve` (separate terminal)
- Moondream model: `ollama pull moondream` (first time only)
- `.env` has `OLLAMA_BASE_URL=http://localhost:11434`

**Test via API**:

**Upload a document**:
```bash
curl -X POST http://127.0.0.1:8000/api/documents/upload \
  -F "file=@/path/to/document.pdf" \
  -F "document_type=invoice"
```

**Expected Response**:
```json
{
  "document_id": "uuid-here",
  "filename": "document.pdf",
  "document_type": "invoice",
  "status": "uploaded",
  "created_at": "2026-04-12T..."
}
```

**List all documents**:
```bash
curl -s http://127.0.0.1:8000/api/documents | jq .
```

**Analyze a document**:
```bash
curl -X POST http://127.0.0.1:8000/api/documents/analyze/{doc_id}
```

**Expected Output** (after Moondream processes):
```json
{
  "document_id": "uuid",
  "analysis": "Extracted text, key fields, summary...",
  "extracted_fields": {
    "invoice_number": "INV-123",
    "amount": "$500.00",
    ...
  },
  "status": "analyzed"
}
```

**Test in UI**:
1. Dashboard → Documents section
2. Click "Upload Document"
3. Select a PDF/image
4. Wait for Moondream analysis
5. Review extracted fields

**Common Issues**:
- Ollama not running: "Connection refused on localhost:11434"
- Model not found: `ollama pull moondream` first
- Large PDF: May take 30+ seconds to process

---

### Pipeline 6: Gmail Integration (Coming Soon)

**Purpose**: Auto-pull emails from Gmail inbox and process them

**Setup Required**:
1. Create Google OAuth credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create new OAuth 2.0 Client (Desktop app)
   - Save as `gmail_credentials.json` in project root
   - **Set in `.env`**: `GOOGLE_APPLICATION_CREDENTIALS=gmail_credentials.json`

2. First run triggers OAuth flow:
   ```bash
   curl http://127.0.0.1:8000/api/pending
   # Browser opens for Gmail consent → Creates `token.json`
   ```

3. Auto-pulls unread emails:
   - Filters: `in:inbox is:unread -category:promotions`
   - Tiers them with Gemini
   - Drafts responses
   - Awaits approval before sending

**Manual Test**:
```bash
curl -X POST http://127.0.0.1:8000/api/search-gmail \
  -H "Content-Type: application/json" \
  -d '{"q": "from:steve.johnson"}'
```

---

### Pipeline 7: Twin Brain (Conversational AI)

**Purpose**: Chat with AI about pending emails, get insights, ask for help

**Test Commands**:

```bash
curl -X POST http://127.0.0.1:8000/api/twin-chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How many urgent emails do I have?",
    "conversation_id": "default"
  }'
```

**Expected Response**:
- AI analyzes pending approvals
- Returns count by tier
- Offers next action suggestions

**Example Queries**:
- "What are my top priority emails?"
- "Draft a response for the DEMO-00001 email"
- "Which tier 1 emails need attention?"
- "Summarize my pending approvals"

---

## Demo Mode Testing (No API Keys)

To test without real Gmail or Gemini:

```bash
# 1. Set demo mode
export DEMO_MODE=1

# 2. Start app
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000

# 3. Dashboard will show seeded demo data
# 4. All API calls work with mock responses
# 5. No real emails sent, no API costs
```

---

## Step-by-Step Full Integration Test (with Gmail)

### Prerequisites

1. **Google OAuth Setup**:
   ```bash
   # 1a. Download credentials from Google Cloud Console
   # 1b. Save as: gmail_credentials.json

   # 1c. Update .env
   GOOGLE_APPLICATION_CREDENTIALS=gmail_credentials.json
   GEMINI_API_KEY=your_key_here
   ```

2. **Start Application**:
   ```bash
   python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```

### Test Sequence

**Step 1: Fetch Gmail Inbox** (OAuth triggers on first call)
```bash
curl http://127.0.0.1:8000/api/pending
# Browser opens → Click "Allow" → token.json created
```

**Step 2: Verify Emails Retrieved**
```bash
curl -s http://127.0.0.1:8000/api/pending | jq '.[] | {sender, subject, tier}'
```

**Step 3: Check AI Drafts Generated**
```bash
curl -s http://127.0.0.1:8000/api/pending | jq '.[] | {ref_id, draft_body}'
```

**Step 4: Approve an Email**
```bash
curl -X POST http://127.0.0.1:8000/api/approve \
  -H "Content-Type: application/json" \
  -d '{"ref_id": "<email-ref-id>"}'
```

**Step 5: Verify Approval Recorded**
```bash
curl -s http://127.0.0.1:8000/api/pending | grep -c "pending"
# Count should decrease by 1
```

---

## Troubleshooting

### 1. "Connection Refused" on localhost:8000

**Cause**: Server not running

**Fix**:
```bash
cd /home/lade/Hackathons/.git/backpocket-mvp
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. "Gmail Credentials Not Found"

**Cause**: Missing `gmail_credentials.json`

**Fix**:
1. Get OAuth credentials from Google Cloud Console
2. Download as JSON
3. Save as `gmail_credentials.json` in project root
4. Set in `.env`: `GOOGLE_APPLICATION_CREDENTIALS=gmail_credentials.json`

### 3. "Gemini API Key Missing"

**Cause**: `.env` lacks `GEMINI_API_KEY`

**Fix**:
1. Get free key: https://aistudio.google.com/app/apikey
2. Add to `.env`: `GEMINI_API_KEY=your-key-here`
3. Restart app: `Ctrl+C`, re-run uvicorn

### 4. "Ollama Connection Refused"

**Cause**: Ollama not running for document analysis

**Fix** (in separate terminal):
```bash
ollama serve
# In first terminal:
ollama pull moondream  # One-time setup
```

### 5. Database Locked / "table is locked"

**Cause**: Two instances writing simultaneously

**Fix**:
```bash
# Kill all Python processes
pkill -f uvicorn
pkill -f "python3.*main"

# Verify DB file is not corrupted
ls -la backpocket.db

# Restart
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
```

---

## Performance Checklist

| Test | Expected | Status |
|------|----------|--------|
| Server startup | < 5 seconds | - |
| API `/pending` response | < 1 second | - |
| Gemini draft generation | 2-5 seconds | - |
| Approval endpoint | < 500ms | - |
| Document upload | < 2 seconds | - |
| Document analysis (Moondream) | 15-60 seconds | - |
| Dashboard load | < 3 seconds | - |

---

## Next Steps

1. **Local Testing** (No API Keys):
   - Run demo mode with seeded data
   - Test all UI controls
   - Verify database persistence

2. **With Gmail OAuth**:
   - Set up Google Cloud credentials
   - Test email sync
   - Verify tier classification

3. **With Gemini API**:
   - Add API key to `.env`
   - Test draft generation quality
   - Monitor API usage

4. **Full Integration**:
   - Enable Ollama for document analysis
   - Test complete workflow: Email → Tier → Draft → Approve
   - Load test with 50+ pending emails

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app, all routes |
| `services/gmail.py` | Gmail OAuth & email fetch |
| `services/gemini.py` | Gemini triage & draft generation |
| `services/database.py` | SQLite operations |
| `services/document_vision.py` | Ollama/Moondream integration |
| `services/twin_brain.py` | Conversational AI |
| `static/index.html` | Dashboard UI |
| `backpocket.db` | SQLite database (pre-seeded) |
| `.env` | API keys (create from `.env.example`) |

---

## Contact & Support

For issues or questions:
1. Check `AGENTS.md` for quick reference
2. Review error logs in application output
3. Check browser console (F12) for frontend errors
4. Verify `.env` has all required keys
