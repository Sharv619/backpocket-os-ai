# BackPocket OS — Audit & Progress Report
## Date: April 18, 2026 | Day 6 of 17-Day Sprint

---

## Git Status

| Remote | URL | Status |
|--------|-----|--------|
| **origin** | Sharv619/backpocket-os-ai | Pushed (d3ec21b) |
| **sharv** | Sharv619/backpocket-mvp | Diverged (legacy) |

**Commits since sprint start (Apr 14):** 50 commits  
**Latest commit:** `d3ec21b` — entity mapping fix, RAG pipeline, inbox draft, voice bugfixes

---

## Codebase Metrics

| Component | Files | Lines |
|-----------|-------|-------|
| Backend (Python) | 35+ | 15,532 |
| Flutter App (Dart) | 26 | 8,170 |
| API Endpoints | 109 | across 14 route files |
| Database Tables | 38 | SQLite |
| Test Files | 2 | 169 lines |

---

## Architecture (Current State)

```
┌─ FastAPI Backend (main.py → 14 route modules)
│  ├─ routes/approvals.py     (8 endpoints)
│  ├─ routes/chat.py          (14 endpoints)
│  ├─ routes/construction.py  (13 endpoints)
│  ├─ routes/voice_commands.py (5 endpoints)
│  ├─ routes/voice.py          (2 endpoints)
│  ├─ routes/email.py          (7 endpoints)
│  ├─ routes/documents.py      (5 endpoints)
│  ├─ routes/instructions.py   (10 endpoints)
│  ├─ routes/marketing.py      (4 endpoints)
│  ├─ routes/mobile.py         (3 endpoints)
│  ├─ routes/utilities.py      (25 endpoints)
│  ├─ routes/integrations.py   (4 endpoints)
│  ├─ routes/admin.py          (2 endpoints)
│  └─ routes/webhook.py        (2 endpoints)
│
├─ Services Layer
│  ├─ gemini.py          — AI draft generation (OpenRouter + Gemini)
│  ├─ twin_engine.py     — 3 AI Twins + RAG (ChromaDB)
│  ├─ voice_session.py   — Voice state machine
│  ├─ intent_classifier.py — 46-intent taxonomy
│  ├─ entity_resolver.py — Fuzzy entity matching
│  ├─ background.py      — Email triage pipeline
│  ├─ construction.py    — Leads/Quotes/Payments CRUD
│  ├─ database.py        — SQLite operations
│  └─ 12 more service modules
│
├─ Flutter Mobile App (26 Dart files)
│  ├─ 11 screens (Dashboard, Inbox, Twin Chat, Docs, Marketing,
│  │              Instructions, Construction, Settings, Voice, VisionChat, VoiceHelp)
│  ├─ 3 widgets (VoiceFAB, RecordingOverlay, ConfirmationCard)
│  ├─ 4 services (ApiService, ApiClient, VoiceCommandService, TtsService)
│  └─ 5 models (Lead, Quote, Payment, PendingEmail, VoiceCommandResponse)
│
└─ ChromaDB Vector Database (~62 documents seeded)
   ├─ admin collection (55 docs)
   ├─ accountant collection (18 docs)
   └─ auditor collection (4 docs)
```

---

## WBS EPIC Progress (Day 6 of 17)

### EPIC A — Foundation: 60% Complete
| Task | Status | Notes |
|------|--------|-------|
| A1. Oracle ARM provisioning | Done | `scripts/oracle-provision.sh` |
| A2. GitHub Actions deploy | Done | `.github/workflows/deploy.yml` |
| A3. Auth IdP ADR | Done | `docs/adr/001-auth.md` |
| A4. Backup to R2 script | Done | `scripts/backup_to_r2.sh` |
| **Actual deploy to Oracle** | NOT DONE | Scripts exist, not executed |

### EPIC B — Voice-to-Quote: 75% Complete
| Task | Status | Notes |
|------|--------|-------|
| B1. Flutter voice capture UI | Done | `voice_input_screen.dart` + mic recording |
| B2. /api/voice/transcribe | Done | `routes/voice.py` |
| B3. /api/voice/quote-from-transcript | Partial | Voice→Lead works, quote gen needs voice trigger |
| B4. Flutter quote review UI | Done | `construction_screen.dart` Quotes tab |
| B5. Prompt engineering | Done | 46-intent taxonomy, tradie slang, entity aliases |

### EPIC C — Billing: 0% Complete
| Task | Status | Notes |
|------|--------|-------|
| C1. Stripe integration | NOT STARTED | No Stripe code exists |
| C2. Flutter billing UI | NOT STARTED | No billing screen |
| C3. WhatsApp nudge logic | Partial | WhatsApp service exists, no billing nudges |

### EPIC E — Data Layer: 35% Complete
| Task | Status | Notes |
|------|--------|-------|
| E1. SQLite→Postgres migration | Done | `scripts/sqlite_to_pg_migration.py` |
| E2. services/postgres_db.py | Done | SQLAlchemy module exists |
| E3. services/pgvector_rag.py | Done | Module exists |
| E4. Dual-write logic | NOT DONE | Still single-write SQLite |
| **Actual Postgres running** | NO | All production queries hit SQLite |

### EPIC F — Auth + RLS: 5% Complete
| Task | Status | Notes |
|------|--------|-------|
| F1. IdP integration code | NOT DONE | ADR written, no code |
| F2. RLS policies | NOT DONE | |
| F3. Token encryption | NOT DONE | Tokens stored as plaintext JSON |
| F4. Caddy security headers | NOT DONE | |

### EPIC G — Photo-to-Post: 30% Complete
| Task | Status | Notes |
|------|--------|-------|
| G1. Flutter camera UI | Partial | `vision_chat_screen.dart` exists |
| G2. /api/vision/analyze_materials | Done | `services/document_vision.py` |
| G3. /api/social/generate_post | Partial | Marketing endpoints exist |
| G4. Flutter social post review UI | Partial | `marketing_screen.dart` exists |

### EPIC H — Security: 0% Complete
| Task | Status | Notes |
|------|--------|-------|
| H1. Privacy policy / TOS | NOT STARTED | |
| H2. OWASP ZAP automation | NOT STARTED | |
| H3. CIS benchmark | NOT STARTED | |

---

## Bugs Fixed This Session

| Bug | Severity | Fix |
|-----|----------|-----|
| Entity→Param mapping failure | **CRITICAL** | Gemini returns `{name,job,suburb}`, PARAM_ORDER expects `{client_name,job_type,location}`. Added ENTITY_ALIASES + _normalize_entities() |
| "5 grand" → 5.0 | HIGH | Added MONEY_WORDS dict + _parse_money() for tradie slang |
| "no email" cancels voice session | HIGH | Changed substring match → exact match for NO_WORDS |
| Document analyze fails | MEDIUM | Handler now checks doc_id, document_id, id aliases + fallback |
| Email detail shows truncated text | MEDIUM | Added `draft_body` to /api/mobile/pending, updated Flutter |
| RAG/ChromaDB empty (zero docs) | HIGH | Created seed_rag.py, wired ingest into triage/approve/revise |

---

## RAG Pipeline (NEW — wired this session)

```
Email arrives → background.py triage → ingest to ChromaDB
User approves → approvals.py/mobile.py → ingest approved draft
User revises → approvals.py → ingest correction + feedback
Next email → gemini.py retrieves 3 relevant chunks → better draft
```
**Seeded:** 62 documents from existing data (drafts, corrections, instructions, leads, action history)

---

## What Works End-to-End

| Flow | Status | Notes |
|------|--------|-------|
| Email Triage → AI Draft → Approve/Revise | WORKS | Desktop + Mobile |
| Voice → Transcribe → Intent → Entity Extract | WORKS | After entity mapping fix |
| Voice → Create Lead | WORKS | Full state machine flow |
| Voice → Create Quote | WORKS | With entity aliases |
| Construction Leads CRUD | WORKS | API + Flutter UI |
| Construction Quotes CRUD | WORKS | API + Flutter UI |
| Construction Payments CRUD | WORKS | API + Flutter UI |
| Twin Chat (Pip) | WORKS | Backend 200, Flutter needs correct server URL |
| Document Upload + Analyze | WORKS | Vision API integration |
| RAG Learning Flywheel | WORKS | Ingest on triage/approve/revise |

---

## What's Broken / Not Working

| Issue | Impact | Fix Needed |
|-------|--------|------------|
| Flutter app on phone → `127.0.0.1` | BLOCKING | User saved wrong server URL in Settings; need to change to `192.168.1.147:8000` |
| voice_response.py says "Analysis complete" on error | LOW | Response generator ignores error status |
| No auth / multi-tenant | BLOCKING for customers | EPIC F not started |
| No Stripe billing | BLOCKING for revenue | EPIC C not started |
| Postgres not deployed | Risk | Scripts exist but not executed |

---

## Overall Sprint Assessment

| Metric | Target | Current | Gap |
|--------|--------|---------|-----|
| Sprint Day | 6 of 17 | Day 6 | On schedule |
| Overall Completion | ~40% (Day 6) | **~45%** | Slightly ahead on features |
| Revenue Features (EPICs B+C) | 50% by Day 7 | 38% | C (Billing) = 0% is critical gap |
| Infrastructure (EPICs A+E) | 60% by Day 7 | 48% | Scripts exist, not deployed |
| Auth/Security (EPICs F+H) | 10% by Day 6 | 3% | Expected — scheduled later |
| Paid Customers | 3 by Day 18 | 0 | Need Stripe + deploy first |

### Risk Assessment
1. **Stripe (EPIC C) not started** — scheduled Day 8-12, but zero code exists. Highest priority gap.
2. **No actual deployment** — Oracle scripts exist but never run. Can't get customers without hosting.
3. **Auth at 5%** — Multi-tenant required before real users. ADR done, code not started.
4. **Phone connectivity** — Flutter app on phone has stale `127.0.0.1` in SharedPreferences.

### Recommendation
Days 7-8 priority: Deploy to Oracle ARM (A1 execute) → Stripe skeleton (C1) → Auth integration (F1). Feature code is ahead; infrastructure is the bottleneck.

---

*Generated: April 18, 2026 | Commit: d3ec21b | Branch: main*
