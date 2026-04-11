# BackPocket OS - Testing Documentation Index

**Last Updated**: 2026-04-12  
**Status**: ✅ Ready for Testing  
**Created Files**: 6 comprehensive guides + 1 diagnostic script

---

## Start Here

### If you have 2 minutes:
Read **[QUICK_TEST.md](./QUICK_TEST.md)**
- How to start the server
- 7 essential test commands
- Quick troubleshooting
- Gmail setup instructions

### If you have 20 minutes:
Follow **[TESTING_CHEATSHEET.txt](./TESTING_CHEATSHEET.txt)**
- Copy-paste test commands
- Common workflows
- Database queries
- One-liners for quick checks

### If you have 60+ minutes:
Read **[TEST_PIPELINES.md](./TEST_PIPELINES.md)**
- Detailed explanation of all 7 pipelines
- Complete setup procedures
- Expected responses for each test
- Performance benchmarks
- Full integration workflow
- Comprehensive troubleshooting

### While Testing:
Reference **[API_REFERENCE.md](./API_REFERENCE.md)**
- Complete API documentation
- All 20+ endpoints with examples
- Request/response formats
- Error handling
- Mobile API endpoints

### For Status Overview:
Review **[TESTING_REPORT.md](./TESTING_REPORT.md)**
- What was verified
- Current configuration
- Pre-populated demo data
- Potential issues & solutions
- Testing checklist

---

## File Overview

### Documentation Files (Guides)

| File | Size | Time | Purpose |
|------|------|------|---------|
| **QUICK_TEST.md** | 5.4 KB | 2 min | Quick start guide for immediate testing |
| **TESTING_CHEATSHEET.txt** | 9.6 KB | 5 min | Copy-paste curl commands and workflows |
| **TEST_PIPELINES.md** | 12 KB | 60 min | Comprehensive pipeline testing guide |
| **API_REFERENCE.md** | 9.7 KB | Reference | Complete API documentation |
| **TESTING_REPORT.md** | 13 KB | Reference | System status and configuration report |
| **TESTING_INDEX.md** | This file | - | Navigation guide (you are here) |

### Script Files

| File | Purpose |
|------|---------|
| `scripts/diagnostic_check.py` | Automated health check (4/4 checks) |
| `scripts/demo_seed.py` | Reset database to demo state |
| `START_DEMO.sh` | One-command launcher |

---

## Quick Navigation

### By Task

**I want to...**

- **Get started immediately** → [QUICK_TEST.md](./QUICK_TEST.md)
- **Run one-liners** → [TESTING_CHEATSHEET.txt](./TESTING_CHEATSHEET.txt)
- **Test specific pipeline** → [TEST_PIPELINES.md](./TEST_PIPELINES.md)
- **Understand an API** → [API_REFERENCE.md](./API_REFERENCE.md)
- **Check system status** → [TESTING_REPORT.md](./TESTING_REPORT.md)
- **Run diagnostic** → `python3 scripts/diagnostic_check.py`

### By Time Available

| Time | Action |
|------|--------|
| **2 min** | Run `python3 scripts/diagnostic_check.py` |
| **5 min** | Follow QUICK_TEST.md steps 1-3 |
| **15 min** | Run all test commands in TESTING_CHEATSHEET.txt |
| **30 min** | Complete "Full Testing" section in QUICK_TEST.md |
| **60+ min** | Deep dive in TEST_PIPELINES.md |

### By Pipeline

Each pipeline has documentation in TEST_PIPELINES.md:

1. **Pending Approvals** - Get emails awaiting action
2. **Email Triage** - AI classification with Gemini
3. **Approval & Response** - Track approvals
4. **Draft Management** - Save/edit responses
5. **Document Analysis** - Upload & analyze with Moondream
6. **Gmail Integration** - Real Gmail sync (optional)
7. **Twin Brain Chat** - Conversational AI

---

## Current Status

### All Systems ✅

- ✅ Dependencies installed
- ✅ Database initialized with 5 demo emails
- ✅ Configuration (.env) set
- ✅ Application ready
- ✅ Demo mode enabled (safe)
- ✅ Diagnostic: 4/4 PASS

### Demo Data Pre-loaded

5 sample emails ready for testing:

| ID | Sender | Tier | Subject |
|----|--------|------|---------|
| DEMO-00001 | steve.johnson@sparkypro.com.au | 1 | Quote for rewire |
| DEMO-00002 | mike.walsh@everflowplumbing.com.au | 1 | Invoice query |
| DEMO-00003 | quotes@bunningsbusiness.com.au | 3 | Trade quote |
| DEMO-00004 | noreply@servicem8.com | 4 | ServiceM8 digest |
| DEMO-00005 | deals@promo-blast.com.au | 5 | Spam |

---

## Getting Started (3 Steps)

### Step 1: Verify System (30 seconds)

```bash
python3 scripts/diagnostic_check.py
# Expected: 4/4 checks passed ✓
```

### Step 2: Start Server (Automatic)

```bash
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
# Expected: Uvicorn running on http://127.0.0.1:8000
```

### Step 3: Test (Pick Your Approach)

**Option A - Quick (2 min)**: Follow [QUICK_TEST.md](./QUICK_TEST.md)

**Option B - Copy-Paste (5 min)**: Use [TESTING_CHEATSHEET.txt](./TESTING_CHEATSHEET.txt)

**Option C - Deep Dive (60 min)**: Follow [TEST_PIPELINES.md](./TEST_PIPELINES.md)

---

## Testing Checklist

Use this while testing:

- [ ] Run diagnostic check → 4/4 PASS
- [ ] Start server on port 8000
- [ ] Open dashboard at http://127.0.0.1:8000/static/index.html
- [ ] Verify 5 demo emails visible
- [ ] Test `/api/pending` endpoint
- [ ] Approve one email
- [ ] Save a draft
- [ ] Upload a document
- [ ] Test twin chat
- [ ] (Optional) Set up Gmail credentials

---

## Document Reading Guide

### QUICK_TEST.md (5.4 KB, 2 min read)

**Best for**: Getting started immediately  
**Contains**:
- TL;DR quick start
- 6 test commands
- Troubleshooting table
- Gmail setup instructions

**Quick outline**:
1. Run diagnostic
2. Start server
3. Open dashboard
4. Run test commands
5. Test with Gmail (optional)

### TESTING_CHEATSHEET.txt (9.6 KB, reference)

**Best for**: Copy-pasting commands  
**Contains**:
- 10 basic API tests (copy-paste ready)
- Gmail integration tests
- Database queries
- One-liners
- Common workflows
- Performance benchmarks

**Quick outline**:
- Start server (Terminal 1)
- Run diagnostic (Terminal 2)
- Copy any curl command
- Get expected output

### TEST_PIPELINES.md (12 KB, 60 min read)

**Best for**: Comprehensive understanding  
**Contains**:
- Detailed explanation of each pipeline
- Requirements for each
- How it works (step-by-step)
- Complete test procedures
- Expected responses
- Known issues & fixes
- Performance checklist
- Full integration workflow

**Quick outline**:
1. 7 pipeline explanations
2. Setup procedures
3. Test commands per pipeline
4. Troubleshooting
5. Performance guide

### API_REFERENCE.md (9.7 KB, reference)

**Best for**: Understanding endpoints  
**Contains**:
- Base URL
- All 20+ API endpoints documented
- Request/response examples
- Query syntax
- Error handling
- Mobile API endpoints
- Complete workflow examples

**Quick outline**:
- Health & status
- Pending approvals
- Approvals & actions
- Draft management
- Documents
- Chat
- Gmail search
- Conversations
- Mobile APIs

### TESTING_REPORT.md (13 KB, reference)

**Best for**: Understanding project status  
**Contains**:
- Executive summary
- What was verified (5 areas)
- Pipeline readiness (7 pipelines)
- Testing guides created
- Configuration details
- Potential issues & solutions
- Next steps
- Reference files list

**Quick outline**:
- Status overview
- Verification results
- Pipeline readiness matrix
- 3 guides created
- Configuration status
- Troubleshooting
- Next steps

---

## Common Questions

**Q: How do I start?**  
A: Read QUICK_TEST.md (2 min) or run TESTING_CHEATSHEET.txt commands

**Q: Is everything working?**  
A: Run `python3 scripts/diagnostic_check.py` - should show 4/4 PASS

**Q: How do I test pipelines?**  
A: Follow TEST_PIPELINES.md or use curl commands from TESTING_CHEATSHEET.txt

**Q: What API endpoints exist?**  
A: See API_REFERENCE.md for complete documentation

**Q: How do I enable Gmail?**  
A: See "Gmail Integration Setup" section in QUICK_TEST.md

**Q: What if something fails?**  
A: See "Troubleshooting" section in TEST_PIPELINES.md or QUICK_TEST.md

**Q: How long does testing take?**  
A: 2 min (quick), 20 min (full), 60+ min (deep dive)

---

## Key Concepts

### Pipelines (7 total)

1. **Pending Approvals** - Inbox of emails needing response
2. **Email Triage** - AI sorts by priority (tier 1-5)
3. **Approval & History** - Mark as done, track actions
4. **Draft Management** - Save, edit, manage responses
5. **Document Analysis** - Upload, analyze with vision AI
6. **Gmail Integration** - Real Gmail inbox (optional)
7. **Twin Brain** - Chat with AI about pending work

### Technologies Used

- **Backend**: FastAPI + Uvicorn
- **Database**: SQLite (backpocket.db)
- **AI**: Gemini (triage) + Moondream (vision)
- **Integration**: Gmail API, Google Sheets
- **Local AI**: Ollama (optional for docs)

### Demo Mode

- Currently **ENABLED** (DEMO_MODE=1 in .env)
- Safe for testing (no real sends)
- Use real APIs by setting DEMO_MODE=0

---

## Support & Troubleshooting

### Quick Fixes

| Problem | Fix |
|---------|-----|
| Port 8000 in use | `lsof -i :8000` then `kill -9 <PID>` |
| Database locked | Kill Python processes and restart |
| Gmail not working | Download credentials, save as `gmail_credentials.json` |
| API timeout | Check server is running in Terminal 1 |
| Module not found | Run `pip install -r requirements.txt` |

### Get Help

1. **Is system ready?** → Run `diagnostic_check.py`
2. **How do I test?** → Read `QUICK_TEST.md` or `TESTING_CHEATSHEET.txt`
3. **What's the API?** → See `API_REFERENCE.md`
4. **Is something broken?** → Check troubleshooting in `TEST_PIPELINES.md`
5. **What's configured?** → See `TESTING_REPORT.md`

---

## Files at a Glance

### Documentation (Read These)
- `QUICK_TEST.md` - Start here (2 min)
- `TESTING_CHEATSHEET.txt` - Commands to copy-paste (5 min)
- `TEST_PIPELINES.md` - Comprehensive guide (60 min)
- `API_REFERENCE.md` - API documentation (reference)
- `TESTING_REPORT.md` - Status report (reference)
- `TESTING_INDEX.md` - This file

### Scripts (Run These)
- `scripts/diagnostic_check.py` - Health check (30 sec)
- `scripts/demo_seed.py` - Reset demo data
- `START_DEMO.sh` - All-in-one launcher

### Configuration
- `.env` - API keys (already configured)
- `.env.example` - Template
- `backpocket.db` - Database (5 demo items pre-loaded)

---

## Next Steps

### Immediate (Now)
1. Read this file (you're reading it! ✓)
2. Read QUICK_TEST.md (2 min)
3. Run diagnostic_check.py (30 sec)

### Short-term (Next 15 min)
1. Start server
2. Run test commands
3. Open dashboard
4. Approve an email
5. Upload a document

### Medium-term (Next hour)
1. Read TEST_PIPELINES.md
2. Test all 7 pipelines thoroughly
3. Verify performance benchmarks
4. Check all error cases

### Long-term (For Production)
1. Set up Gmail credentials (optional)
2. Enable Ollama for document analysis
3. Configure real API keys
4. Disable demo mode (DEMO_MODE=0)
5. Load test with real data

---

## Summary

**Everything is ready to test.**

You have:
- ✅ All documentation
- ✅ Diagnostic tools
- ✅ Demo data (5 emails)
- ✅ Working application
- ✅ Configured APIs

**Start with**: [QUICK_TEST.md](./QUICK_TEST.md) (2 min)  
**Then try**: [TESTING_CHEATSHEET.txt](./TESTING_CHEATSHEET.txt) (5 min)  
**Deep dive**: [TEST_PIPELINES.md](./TEST_PIPELINES.md) (60 min)

**To enable Gmail**: Get OAuth credentials and update `.env`

**Questions?** Check the relevant guide above.

---

**Created**: 2026-04-12  
**Project**: BackPocket OS - Life Automation Portal  
**Status**: Production Ready for Testing  

**Let's go! 🚀**
