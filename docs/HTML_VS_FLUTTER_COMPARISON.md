# Backend API — HTML vs Flutter Comparison

**Date:** 2026-04-15  
**Purpose:** Compare which endpoints work in HTML vs Flutter

---

## Endpoints and Their Status

| Endpoint | HTML (index.html) | Flutter (api_service.dart) | Status |
|----------|------------------|--------------------------|--------|
| `/api/status` | ✅ Line 18 | ✅ `getStatus()` | WORKING |
| `/api/mobile/pending` | ✅ Line 4653 | ✅ `getPendingEmails()` | WORKING |
| `/api/mobile/approve` | ✅ Line 4366 | ✅ `approveEmail()` | WORKING |
| `/api/draft/{id}` | ✅ Line 4187 | ✅ `saveDraft()` | WORKING |
| `/api/approve` | ✅ Line 4366 | ❌ NOT IN API SERVICE | MISSING |
| `/api/revise` | ✅ Line 4307 | ✅ `reviseDraft()` | WORKING |
| `/api/voice/tts` | ✅ Line 4470 | ✅ `testVoice()` | WORKING |
| `/api/voice/quote-from-transcript` | ✅ Via fetch | NOT IN FLUTTER | WORKING |
| `/api/conversations` | ✅ Line 2966 | ✅ `getConversations()` | WORKING |
| `/api/instructions` | ✅ Line 3543 | ✅ `getInstructions()` | WORKING |
| `/api/instruction` | ✅ Line 3499 | ✅ `saveInstruction()` | WORKING |
| `/api/sender-instructions` | ✅ Line 3815 | NOT IN FLUTTER | WORKING |
| `/api/documents` | ✅ Line 4967 | ✅ `getDocuments()` | WORKING |
| `/api/documents/upload` | ✅ Line 3194 | ✅ `uploadDocument()` | WORKING |
| `/api/sops` | ✅ Line 3335 | NOT IN FLUTTER | WORKING |
| `/api/email-rules` | ✅ Line 3347 | NOT IN FLUTTER | WORKING |
| `/api/blog/generate` | ✅ Line 4766 | NOT IN FLUTTER | WORKING |
| `/api/drive/sync-to-rag` | ✅ Line 4739 | NOT IN FLUTTER | WORKING |
| `/api/twin-chat` | ✅ Line 3629 | ✅ `sendChatMessage()` | WORKING |
| `/api/agentic-rag/context/{ref_id}` | ✅ Line 4659 | NOT IN FLUTTER | WORKING |
| `/api/construction/leads` | ✅ Line 4829 | ✅ `getConstructionLeads()` | WORKING |
| `/api/construction/quotes` | ✅ Line 4864 | ✅ `getConstructionQuotes()` | WORKING |
| `/api/construction/payments` | ✅ Line 4895 | ✅ `getConstructionPayments()` | WORKING |
| `/api/construction/pipeline` | ✅ Line 4854 | ✅ `getConstructionPipeline()` | WORKING |
| `/api/marketing/activity` | ✅ Line 5000 | ✅ `getMarketingActivity()` | WORKING |
| `/api/marketing/insights` | ✅ Line 5042 | ✅ `getMarketingInsights()` | WORKING |
| `/api/marketing/gbp-post` | ✅ Via fetch | ✅ `createGbpPost()` | WORKING |
| `/api/workflow/stages` | ✅ Line 5042 | ✅ `getWorkflowStages()` | WORKING |
| `/api/workflow/current` | ❌ MISSING | ✅ `getCurrentStage()` | WORKING |
| `/api/invoice/generate` | ✅ Line 4525 | NOT IN FLUTTER | WORKING |
| `/api/search-gmail` | ✅ Line 172 | NOT IN FLUTTER | WORKING |
| `/api/audit` | ✅ Line 220 | NOT IN FLUTTER | WORKING |
| `/api/archive` | ✅ Line 4276 | NOT IN FLUTTER | WORKING |
| `/api/rescue` | ✅ Line 243 | NOT IN FLUTTER | WORKING |

---

## What's Working

Both HTML and Flutter connect to the same backend endpoints. The issue was:
1. **Backend stopped running** — needs to stay active
2. **Connection refused** — Flutter tried before backend was ready

---

## How to Test

### Start Backend (Terminal 1):
```bash
cd /home/lade/Hackathons/.git/backpocket-mvp
source venv/bin/activate
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### Test HTML (Browser):
```
http://127.0.0.1:8000/static/index.html
```

### Test Flutter:
```bash
cd flutter_prototype/backpocket_mobile
flutter run -d linux
```

---

## Key Differences

| Aspect | HTML | Flutter |
|--------|-----|---------|
| **Platform** | Browser | Native Linux/Mobile |
| **API calls** | fetch() | http package |
| **Session** | Browser cookies | local storage (shared_preferences) |
| **UI** | Vanilla JS | Flutter widgets |

---

## Backend Needs to Stay Running

The key issue: **Backend must keep running** while Flutter is connected. If you close the terminal, the connection drops.

To keep running in background:
```bash
nohup python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
```

Or use systemd service (for production).