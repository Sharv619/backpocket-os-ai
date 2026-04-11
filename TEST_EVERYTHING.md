# BackPocket MVP - Complete Testing Guide

Test all features, workflows, and integrations.

---

## ✅ What's Implemented & Working

### Email & Drafts
- ✅ Gmail OAuth connection
- ✅ Email reading & triage
- ✅ **AI Draft Generation** (just fixed!)
- ✅ Learned patterns storage
- ✅ Three AI twins (Accountant, Auditor, Admin)

### Document/Vision Processing
- ✅ Document upload (`POST /api/documents/upload`)
- ✅ Vision analysis (`POST /api/documents/analyze/{doc_id}`)
- ✅ Image/PDF processing
- ✅ Invoice extraction

### Data Integration
- ✅ Google Sheets connection
- ✅ Google Drive sync
- ✅ Data retrieval

### Workflows (Designed, Not Yet Implemented)
- 📋 **Documented**: 7 complete workflows with API specs
  - Social Media Posting (4 steps)
  - Content Calendar (5 steps)
  - Analytics & Reporting (4 steps)
  - Newsletter Campaigns (5 steps)
  - Lead-to-Scope Extractor (construction)
  - Tradie Persona Follow-ups (construction)
  - Site Note to Action Items (construction)
- ⏳ **Not yet implemented**: Endpoints need to be added to main.py

### Camera/Real-Time Vision
- ❌ **Not implemented**: Currently document upload only (static files)
- 🔄 **Possible**: Can be added via browser camera API + FastAPI endpoint

---

## 🧪 Quick Test Plan

### Test 1: Draft Generation (5 min)
```bash
python3 test_draft.py
```
**Expected**: ✅ Should generate professional email draft

### Test 2: OpenRouter API (2 min)
```bash
python3 test_openrouter.py
```
**Expected**: ✅ Should connect and respond

### Test 3: Email Importing (10 min)
```bash
python3 import_real_emails.py
```
**Expected**: ✅ Should fetch emails and generate drafts

### Test 4: Server Health (2 min)
```bash
curl http://127.0.0.1:8000/api/health
```
**Expected**: ✅ Should return `{"status":"healthy"}`

### Test 5: Document Upload & Vision (5 min)
1. Go to dashboard: `http://127.0.0.1:8000/static/index.html`
2. Upload an invoice image
3. Click "Analyze"
**Expected**: ✅ Should extract invoice details

---

## 📋 Test Checklist

### Setup Tests
- [ ] Server starts without errors
- [ ] Dashboard loads at `http://127.0.0.1:8000/static/index.html`
- [ ] No "Steve" references in dashboard
- [ ] Background is dark purple/blue gradient

### Gmail Integration
- [ ] Can fetch unread emails: `curl http://127.0.0.1:8000/api/search-gmail`
- [ ] Can import real emails: `python3 import_real_emails.py`
- [ ] Drafts generate without errors

### AI/LLM Tests
- [ ] OpenRouter API key works: `python3 test_openrouter.py`
- [ ] Draft generation works: `python3 test_draft.py`
- [ ] Learned patterns apply to similar emails

### Document/Vision Tests
- [ ] Can upload document: `POST /api/documents/upload`
- [ ] Can analyze document: `POST /api/documents/analyze/{doc_id}`
- [ ] Invoice extraction works
- [ ] Image processing works

### Dashboard Tests
- [ ] All sidebar sections appear
- [ ] New sections show (AGENTIC RAG, BLOG, DRIVE)
- [ ] Navigation toggle functions work
- [ ] Chat interface works
- [ ] Can approve/reject drafts

---

## 🎬 Live Testing Script

```bash
#!/bin/bash

echo "🧪 BackPocket MVP Test Suite"
echo "=============================="
echo ""

# Test 1: Server Health
echo "Test 1: Server Health"
curl -s http://127.0.0.1:8000/api/health | jq .
echo ""

# Test 2: Draft Generation
echo "Test 2: Draft Generation"
python3 test_draft.py
echo ""

# Test 3: OpenRouter
echo "Test 3: OpenRouter API"
python3 test_openrouter.py
echo ""

# Test 4: Gmail Connection
echo "Test 4: Gmail Connection"
curl -s http://127.0.0.1:8000/api/search-gmail | jq '.[] | {from, subject}' | head -10
echo ""

echo "✅ Basic tests complete!"
```

---

## 📱 Testing Without Real Gmail

If you don't want to connect real Gmail, use demo data:

```bash
# Clear existing data
sqlite3 backpocket.db "DELETE FROM pending_approvals;"

# Seed with demo data
python3 << 'EOF'
import services.database as db
from datetime import datetime
import uuid

conn = db.sqlite3.connect(db.DB_PATH)
cursor = conn.cursor()

# Insert demo emails
demo_emails = [
    ("john@supplier.com", "Invoice #2024-001", "Hi, please find attached invoice for $1500", 1),
    ("admin@taxagency.com", "BAS Notice", "Your BAS is due by end of month", 2),
    ("client@example.com", "Quote Request", "Can you quote for kitchen reno?", 1),
]

for sender, subject, snippet, tier in demo_emails:
    cursor.execute("""
        INSERT INTO pending_approvals
        (ref_id, sender, subject, snippet, tier, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (f"DEMO-{uuid.uuid4().hex[:8]}", sender, subject, snippet, tier, datetime.now().isoformat()))

conn.commit()
conn.close()
print("✅ Demo data inserted")
EOF
```

---

## 🎥 Camera Integration (Optional Future)

To add **real-time camera vision** (not currently implemented):

```javascript
// In browser (index.html)
// Request camera access
navigator.mediaDevices.getUserMedia({ video: true })
  .then(stream => {
    // Display in <video> element
    const video = document.getElementById('camera-feed');
    video.srcObject = stream;
    
    // Capture frame and send to /api/documents/analyze
  })
  .catch(err => console.error('Camera access denied'));
```

```python
# In main.py (would need to be added)
@app.post("/api/camera/capture")
async def capture_and_analyze(frame: bytes):
    """Analyze frame from camera in real-time"""
    from services.document_vision import analyze_frame
    return analyze_frame(frame)
```

**Current State**: Not implemented
**Timeline**: Can be added in next phase if needed

---

## 🔄 Workflow Testing

### Social Media Workflow (When Implemented)
```bash
# Test endpoint (once implemented)
curl -X POST http://127.0.0.1:8000/api/socials/draft \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "linkedin",
    "content": "Just launched new feature!",
    "hashtags": ["startup", "tech"]
  }'
```

### Construction Workflow (When Implemented)
```bash
# Lead extraction (once implemented)
curl -X POST http://127.0.0.1:8000/api/construction/extract-lead \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Kitchen renovation",
    "body": "Hi, we need kitchen reno. Budget $15k, timeline 2-3 months"
  }'
```

---

## 📊 Test Results Template

```
Date: 2024-04-12
Version: MVP v1.0

✅ Passing:
- Draft generation
- OpenRouter API
- Email import
- Dashboard UI
- Document upload
- Vision analysis

❌ Not Yet Implemented:
- Workflow endpoints
- Camera real-time capture
- Social media API integration
- Analytics dashboards

⚠️ Needs Configuration:
- SPREADSHEET_ID (your Google Sheet)
- WHAPI_TOKEN (if using WhatsApp)
- Ollama (if using local AI)

Notes:
- All core functionality working
- Workflows documented, code not yet added
- Camera can be added in next phase
- Ready for production use
```

---

## 🚀 Next Phase Tasks

1. **Implement Workflow Endpoints** (Priority: High)
   - Add social media workflow endpoints
   - Add content calendar endpoints
   - Add analytics endpoints
   - Add newsletter endpoints

2. **Add Construction Workflows** (Priority: High)
   - Implement lead extraction logic
   - Add tradie persona prompts
   - Build site note processing

3. **Add Camera/Real-Time Vision** (Priority: Medium)
   - Browser camera API integration
   - Real-time frame analysis
   - Mobile camera support (Flutter)

4. **Build Workflow UI** (Priority: Medium)
   - Frontend components for workflows
   - Dashboard for workflow execution
   - Progress tracking

5. **Testing & QA** (Priority: High)
   - Unit tests for each workflow
   - Integration tests
   - Load testing
   - User acceptance testing

---

## 📝 Issue Tracker

### Known Issues
1. **Workflows documented, not implemented** - Need to add endpoints to main.py
2. **Camera not working** - Not built yet, can be added
3. **SPREADSHEET_ID needs config** - User must add their actual Google Sheet ID

### Fixed Issues
- ✅ Draft generation error (OpenRouter model fixed)
- ✅ Steve avatar removed
- ✅ Background improved
- ✅ Duplicate API keys cleaned up

---

## 💬 Testing Notes

**When testing workflows:**
- Workflows are FULLY DESIGNED in documentation
- API endpoints need to be implemented in `main.py`
- Database tables and schemas are defined
- Test data/mock data available

**When testing camera:**
- Not currently implemented
- Can be added via browser `getUserMedia()` API
- Would need backend endpoint to handle frames
- Estimated: 2-3 hours to implement

**When testing construction features:**
- Specialized prompts are documented
- Integration points identified
- Can implement as standalone features

---

## ✨ What You Can Test Right Now

1. ✅ Email automation (works)
2. ✅ Draft generation (works)
3. ✅ Document/image analysis (works)
4. ✅ Dashboard UI (works)
5. ✅ Three AI twins (work)
6. ✅ Google integration (works)
7. ❌ Workflow endpoints (not implemented yet)
8. ❌ Camera real-time (not implemented yet)

---

## 📞 Support

See `backpocket.docs/TROUBLESHOOTING.md` if tests fail.

Good luck with testing! 🚀
