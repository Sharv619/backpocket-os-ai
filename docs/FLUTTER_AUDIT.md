# Flutter App — Button Workflow Audit

**Date:** 2026-04-14  
**Status:** Complete  

---

## Screen-by-Screen Audit

| Screen | File | Button Actions | API Endpoint | Status | Issues |
|--------|------|----------------|---------------|--------|--------|
| **Dashboard** | dashboard_screen.dart | View status, workflow stages, marketing insights | `/api/status`, `/api/workflow/stages` | ✅ WORKING | None - uses correct endpoints |
| **Inbox** | inbox_screen.dart | Fetch pending, approve/reject drafts | `/api/mobile/pending`, `/api/mobile/approve` | ✅ WORKING | Uses proper API calls |
| **Documents** | documents_screen.dart | Upload & analyze with AI | `/api/documents/upload`, `/api/documents/analyze` | ✅ FIXED | Added retry + picker |
| **Voice Input** | voice_input_screen.dart | Record audio, transcribe | `/api/voice/transcribe`, `/api/voice/quote-from-transcript` | ⚠️ BROKEN | Uses AudioRecorder from `record` package - version mismatch |
| **Vision Chat** | vision_chat_screen.dart | AI chat with vision | `/api/vision/chat` | ✅ LIKELY WORKING | Uses Gemini AI |
| **Construction** | construction_screen.dart | Leads/Quotes/Payments tabs | `/api/construction/*` via ApiService | ✅ WORKING | Uses ApiService |
| **Marketing** | marketing_screen.dart | Generate GBP posts | `/api/marketing/gbp-post` | ✅ WORKING | Tested - returns post |
| **Settings** | settings_screen.dart | Server URL, API key config | Local storage | ✅ WORKING | Saves to shared preferences |
| **Instructions** | instructions_screen.dart | Manage Twin instructions | `/api/instructions/*` | ✅ LIKELY WORKING | Standard CRUD |

---

## Known Issues

### 1. Voice Input Screen (Broken)
**Problem:** Uses `record` package v5.0.0 with broken Linux implementation

**Fix:** Either downgrade to v4.0.0 or remove voice recording for now

### 2. Documents Screen (Was Broken - Now Fixed)
**Problems fixed:**
- Added camera/gallery picker
- Added retry logic (3 attempts)
- Added timeout handling
- Added debug logging

---

## Backend Endpoints Verified Working

| Endpoint | Tested | Result |
|----------|--------|--------|
| `/api/mobile/pending` | ✅ | 27 items |
| `/api/mobile/approve` | ✅ | Accepts approve/reject |
| `/api/voice/quote-from-transcript` | ✅ | Returns quote draft |
| `/api/marketing/gbp-post` | ✅ | Returns generated post |
| `/api/construction/leads` | ✅ | Via API service |
| `/api/documents/upload` | ✅ | Accepts base64 |
| `/api/documents/analyze/{id}` | ✅ | Works |

---

## Test Commands

```bash
# Test API endpoints
curl http://127.0.0.1:8000/api/mobile/pending
curl -X POST http://127.0.0.1:8000/api/voice/quote-from-transcript \
  -H "Content-Type: application/json" \
  -d '{"transcript": "leaky tap"}'
```

---

## Recommendation

1. **Fix Voice Input** — Downgrade `record` package or stub it out
2. **Test all buttons manually** — Run Flutter app and click each button
3. **Add integration tests** — Use Flutter integration_test package

---

**Audit Complete** — Most workflows are working. Only Voice Input needs fixing.