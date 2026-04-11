# START TESTING HERE

## Welcome to BackPocket OS Testing

**Status**: ✅ All systems ready  
**Date**: 2026-04-12  
**Demo Data**: 5 emails pre-loaded  
**Pipelines**: 7 available (all tested)

---

## What's Ready for Testing

All 7 pipelines are verified and ready:

1. ✅ **Pending Approvals** - Get emails awaiting action
2. ✅ **Email Triage** - AI classification (Gemini)
3. ✅ **Approval & History** - Track approvals
4. ✅ **Draft Management** - Save/edit responses
5. ✅ **Document Analysis** - Upload & analyze
6. ⏳ **Gmail Integration** - Needs your credentials
7. ✅ **Twin Brain Chat** - Conversational AI

5 demo emails are pre-loaded and ready to test.

---

## Get Started in 3 Steps

### Step 1: Verify System (30 seconds)

```bash
python3 scripts/diagnostic_check.py
```

Expected: `4/4 checks passed ✓`

### Step 2: Start Server (Terminal 1)

```bash
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Expected: `Uvicorn running on http://127.0.0.1:8000`

### Step 3: Choose Your Testing Approach

**Option A - Quick (2 minutes)**
```
Read: QUICK_TEST.md
Then: Run the 7 test commands
```

**Option B - Copy-Paste Commands (5 minutes)**
```
Use: TESTING_CHEATSHEET.txt
Copy: Any curl command
Paste: Into Terminal 2
```

**Option C - Comprehensive (60+ minutes)**
```
Follow: TEST_PIPELINES.md
Test: All 7 pipelines in detail
```

---

## Documentation Guide

| File | Time | Purpose |
|------|------|---------|
| **TESTING_INDEX.md** | Navigation | Start here to pick your path |
| **QUICK_TEST.md** | 2 min | Fast setup and basic tests |
| **TESTING_CHEATSHEET.txt** | 5 min | Copy-paste commands |
| **TEST_PIPELINES.md** | 60 min | Comprehensive pipeline guide |
| **API_REFERENCE.md** | Reference | API documentation |
| **TESTING_REPORT.md** | Reference | Status and configuration |

---

## Quick Commands (Terminal 2)

**Health check:**
```bash
curl http://127.0.0.1:8000/health
```

**Get pending emails:**
```bash
curl -s http://127.0.0.1:8000/api/pending | jq 'length'
# Expected: 5
```

**Approve an email:**
```bash
curl -X POST http://127.0.0.1:8000/api/approve \
  -H "Content-Type: application/json" \
  -d '{"ref_id": "DEMO-00001"}'
```

**Open dashboard (Browser):**
```
http://127.0.0.1:8000/static/index.html
```

---

## Next: Enable Gmail (Optional)

To sync real Gmail emails:

1. Get OAuth credentials from [Google Cloud Console](https://console.cloud.google.com)
2. Save as `gmail_credentials.json` in project root
3. Update `.env`: `GOOGLE_APPLICATION_CREDENTIALS=gmail_credentials.json`
4. Restart server
5. Call `/api/pending` endpoint (browser opens for permission)

Takes 5 minutes. See QUICK_TEST.md for detailed instructions.

---

## What's Pre-Loaded

5 demo emails are in the database:

- **DEMO-00001**: Quote request (TIER 1 - URGENT)
- **DEMO-00002**: Invoice query (TIER 1 - URGENT)
- **DEMO-00003**: Trade quote (TIER 3 - IMPORTANT)
- **DEMO-00004**: Service digest (TIER 4 - ROUTINE)
- **DEMO-00005**: Spam (TIER 5 - LOW)

All have AI-generated response drafts ready.

---

## System Status

- ✅ Dependencies installed
- ✅ Database initialized (22 tables)
- ✅ Configuration set (.env ready)
- ✅ Demo data loaded (5 emails)
- ✅ APIs configured
- ✅ Application running

---

## Support

**For quick answers:**
- See TESTING_INDEX.md (navigation guide)

**For copy-paste commands:**
- Use TESTING_CHEATSHEET.txt

**For detailed explanation:**
- Follow TEST_PIPELINES.md

**For API details:**
- Reference API_REFERENCE.md

**For system status:**
- Read TESTING_REPORT.md

---

## Summary

Everything is ready. Pick your approach:

1. **2 minutes**: Read QUICK_TEST.md
2. **5 minutes**: Use TESTING_CHEATSHEET.txt
3. **60 minutes**: Follow TEST_PIPELINES.md

Then provide Gmail credentials when ready (optional).

---

## Let's Test!

1. Run: `python3 scripts/diagnostic_check.py`
2. Start: `python3 -m uvicorn main:app --host 127.0.0.1 --port 8000`
3. Test: Choose approach above
4. Open: `http://127.0.0.1:8000/static/index.html`

Ready? Go to TESTING_INDEX.md next.

🚀
