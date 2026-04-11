# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview: BackPocket MVP

**BackPocket** is an AI-powered business automation platform for construction/tradie businesses. It integrates with Gmail, Google Drive, and Google Sheets to automate lead capture, quote generation, and business workflow management.

**Current Status**: MVP complete with core automation + construction features (as of Apr 12, 2026)  
**Tech Stack**: Python 3.12, FastAPI, SQLite, OpenRouter AI, Google APIs  
**Main Branch**: main (GitHub: Sharv619/backpocket-mvp)

---

## Architecture Overview

### System Design

```
┌─ Gmail + Drive Integration
│  └─ Receives customer emails
│     └─ Extracts leads/scope
│
├─ AI Twin System (3 specialized personas)
│  ├─ Accountant Twin (financial analysis)
│  ├─ Auditor Twin (data validation)
│  └─ Admin Twin (workflow orchestration)
│
├─ Agentic RAG (Retrieval-Augmented Generation)
│  └─ ChromaDB vector database
│  └─ Learns from past decisions/emails
│
├─ Construction Features (NEW)
│  ├─ Lead Management (leads table)
│  ├─ Quote Pipeline (quotes + cost calculations)
│  ├─ Payment Tracking (payments table)
│  └─ AI Lead Extraction + Tradie Follow-ups
│
└─ Frontend Dashboard (HTML/CSS/JS)
   └─ React-like modular sections
   └─ Real-time data from /api endpoints
```

### Core Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **FastAPI App** | REST API server, routes requests | main.py (4300+ lines) |
| **Database** | SQLite with 22+ tables + construction tables | backpocket.db, services/database.py |
| **Gmail Service** | OAuth 2.0 auth, email processing | services/gmail.py |
| **AI Models** | OpenRouter + Gemini API wrappers | services/gemini.py |
| **Agentic RAG** | Vector DB + learned patterns | services/agentic_rag.py |
| **Construction Manager** | Leads, quotes, payments CRUD | services/construction.py (NEW) |
| **Document Vision** | Invoice/image analysis | services/document_vision.py |
| **Drive Integration** | Google Drive file access | services/drive_integration.py |
| **Google Sheets** | Sync business data to sheets | services/google_sheets.py |
| **Frontend** | Single-page HTML dashboard | static/index.html |

---

## Key Architectural Decisions

### 1. **Three AI Twins System**
- **Accountant Twin**: Analyzes financial data, budgets, costs
- **Auditor Twin**: Validates data quality, flags inconsistencies
- **Admin Twin**: Orchestrates workflows, manages state
- Each has learned patterns stored in the database (session/memory)
- Enables specialized reasoning without prompt juggling

### 2. **Agentic RAG Pipeline**
- Uses ChromaDB for semantic search over past decisions
- RAG pulls relevant context before AI generation
- Learns from corrections: "You said X but should have said Y"
- Prevents hallucinations on repeated tasks

### 3. **Construction Features (Phase 4-5 of MVP)**
- **Lead Extraction**: AI parses emails → auto-creates leads with job_type, budget, urgency
- **Quote Generation**: Materials + Labor + Markup formula with auto-cost calculations
- **Tradie Persona**: AI generates friendly (not corporate) follow-up messages
- **Pipeline Tracking**: Status flow (new → quoted → accepted → invoiced)
- Tables: `leads`, `quotes`, `payments`, `job_files`, `site_visits`

### 4. **OpenRouter API for Cost Optimization**
- Uses "openrouter/auto" model selector for intelligent routing
- Cheaper than direct Gemini API calls
- Supports fallbacks if primary model unavailable
- API key stored in `.env` (never in code)

### 5. **Single-Page Dashboard**
- No React/Vue build step — vanilla JavaScript + HTML sections
- Toggle visibility with sidebar nav items
- Fetch data from `/api/construction/*` endpoints
- Auto-loads on page init: `document.addEventListener('DOMContentLoaded', ...)`

---

## Database Schema

### Core Business Tables
- **leads** (id, client_name, email, job_type, location, urgency, estimated_budget, status, created_at)
- **quotes** (id, lead_id, client_name, job_type, materials_cost, labor_cost, markup_percent, total_amount, status, sent_date, accepted_date)
- **payments** (id, quote_id, client_name, amount, status, due_date, received_date)
- **job_files** (id, quote_id, file_name, file_path, file_type, category)
- **site_visits** (id, quote_id, visit_date, transcript, materials_list, subcontractors_list)

### AI/Memory Tables
- **session_memory** (id, session_id, memory_type, data, learned_pattern, confidence, created_at)
- **email_interactions** (id, email_id, sender, subject, body, extracted_data, ai_response, created_at)
- **learned_patterns** (id, pattern_type, pattern_data, confidence_score, usage_count)
- **audit_log** (id, action, details, timestamp)

### Integration Tables
- **gmail_integration** (id, user_id, access_token, refresh_token, email_address, last_sync)
- **sheets_integration** (id, sheet_id, worksheet_name, sync_status, last_updated)
- **drive_integration** (id, folder_id, folder_name, sync_status)

---

## How to Run

### 1. **Setup Environment**
```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file (copy from .env.example)
cp .env.example .env

# Add API keys:
# - OPENROUTER_API_KEY=sk-or-v1-...
# - GEMINI_API_KEY=...
# - GMAIL_CLIENT_ID=... (from Google Cloud)
# - GMAIL_CLIENT_SECRET=...
```

### 2. **Initialize Database**
```bash
# Create construction tables
python3 scripts/create_construction_tables.py

# Seed with test data (optional)
python3 scripts/demo_seed.py
```

### 3. **Start Server**
```bash
# Development (auto-reload)
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Production
python3 main.py  # Runs uvicorn config from if __name__ == "__main__"
```

### 4. **Access Dashboard**
- **URL**: http://127.0.0.1:8000/
- **Sidebar**: Toggle sections (Leads, Quotes, Payments, Files)
- **Live Data**: Fetches from `/api/construction/*` endpoints

---

## Key API Endpoints

### Construction Features (NEW)
```
POST   /api/construction/leads                    Create lead
GET    /api/construction/leads                    List all leads
GET    /api/construction/leads/{id}               Get lead details
PATCH  /api/construction/leads/{id}               Update lead status

POST   /api/construction/quotes                   Create quote
GET    /api/construction/quotes                   List all quotes
GET    /api/construction/quotes/{id}              Get quote details
PATCH  /api/construction/quotes/{id}              Update quote status

GET    /api/construction/pipeline                 Pipeline summary (totals, revenue)
POST   /api/construction/payments                 Record payment received
GET    /api/construction/payments                 List payments

POST   /api/construction/leads/extract            AI: Extract lead from email
POST   /api/construction/quotes/{id}/tradie-followup   AI: Generate follow-up message
```

### Existing Core Endpoints
- `GET /` - Serve frontend (index.html)
- `POST /api/chat` - Chat with AI twins (Accountant/Auditor/Admin)
- `POST /api/draft-email` - AI draft email responses
- `GET /api/gmail/authenticate` - Gmail OAuth flow
- `POST /api/upload-invoice` - Vision API processing
- `POST /api/google-sheets/sync` - Push data to sheets
- See API_REFERENCE.md for complete list

---

## Development Workflow

### Adding a New Feature

1. **Database**: Add table(s) to `services/database.py` and `scripts/create_construction_tables.py`
2. **Service Logic**: Create module in `services/` with business logic
3. **API Endpoint**: Add route to `main.py` that calls service
4. **Frontend**: Add HTML section + CSS + JavaScript fetch to `static/index.html`
5. **Test**: Use `/api/*` endpoints directly via curl or Postman

### Modifying AI Behavior

- **Twin Prompts**: See `services/gemini.py` — search for `ACCOUNTANT_SYSTEM_PROMPT` (and others)
- **Lead Extraction**: `main.py:4299` — search for `Lead-to-Scope Extractor` prompt
- **Tradie Follow-up**: `main.py:4389` — search for `Tradie Persona Follow-up` prompt
- **Model Used**: "openrouter/auto" — change in `_draft_response_openrouter()` if needed

### Common Tasks

| Task | Command |
|------|---------|
| Run tests | `python3 -m pytest tests/` (if test suite exists) |
| Check syntax | `python3 -m py_compile main.py` |
| View database | `sqlite3 backpocket.db` |
| Check logs | `tail -f /tmp/server.log` |
| Kill hung server | `pkill -f "python3 main.py"` |
| Fresh start | `rm backpocket.db && python3 scripts/create_construction_tables.py && python3 main.py` |

---

## Important Implementation Details

### OpenRouter API
- **Endpoint**: `https://openrouter.ai/api/v1/chat/completions`
- **Auth**: `Authorization: Bearer $OPENROUTER_API_KEY`
- **Key Setting**: Include `"HTTP-Referer": "backpocket.ai"` in headers
- **Model Selection**: "openrouter/auto" — let OpenRouter pick best model
- **Cost**: Much cheaper than direct API calls; OpenRouter negotiates better rates

### AI Lead Extraction Flow
1. Email arrives → `/api/construction/leads/extract` endpoint
2. Prompt sent to OpenRouter with email (subject + body)
3. AI returns JSON: `{client_name, job_type, location, scope_items, urgency, estimated_budget}`
4. JSON parsed and lead created in database
5. Response includes `lead_id` for immediate quote creation

### Tradie Follow-up Message Generation
1. `/api/construction/quotes/{id}/tradie-followup` called
2. Fetches quote details from database
3. Prompt includes: client name, job type, tone guidelines (friendly, not corporate)
4. AI returns single message (max 60 words)
5. No database update — caller decides what to do with message

### Dashboard Data Loading
- **On Page Load**: `loadLeads()`, `loadPipeline()`, `loadPayments()` fire automatically
- **On Refresh Click**: Button calls `refreshLeads()` → clears previous data → calls `loadLeads()`
- **Error Handling**: Fetch errors logged to console, empty state shown ("No leads yet")

### Authentication
- **Gmail OAuth**: User clicks "Connect Gmail" → redirects to Google consent → returns `refresh_token`
- **Token Refresh**: Auto-refreshes when expired (handled in `services/gmail.py`)
- **Frontend**: No auth needed — server is single-user (local assumption)

---

## Critical Files & Line Numbers

| File | Key Sections |
|------|--------------|
| main.py | Line 4127+ Construction endpoints, 765 OpenRouter call, 2014 startup, 4300 if __name__ |
| services/construction.py | ConstructionManager class, all CRUD methods |
| services/gemini.py | _draft_response_openrouter() at line 765 |
| static/index.html | Sections added before closing </main>, CSS before </style>, JS before </script> |
| services/database.py | Table creation and schema definitions |
| .env | All API keys (NEVER commit this) |

---

## Testing

### Manual Testing (No Test Suite Yet)

```bash
# Test lead creation
curl -X POST http://127.0.0.1:8000/api/construction/leads \
  -H "Content-Type: application/json" \
  -d '{"client_name":"John","email":"john@example.com","job_type":"Kitchen","location":"Sydney","urgency":"high","estimated_budget":15000}'

# Test AI extraction
curl -X POST http://127.0.0.1:8000/api/construction/leads/extract \
  -H "Content-Type: application/json" \
  -d '{"from":"customer@example.com","subject":"Need kitchen reno","body":"Looking to renovate. Budget 12k. Area: Penrith."}'

# Test follow-up generation
curl -X POST http://127.0.0.1:8000/api/construction/quotes/1/tradie-followup
```

### Dashboard Testing
1. Open http://127.0.0.1:8000/
2. Click "📩 LEADS" in sidebar — should see test lead
3. Click "💰 QUOTES" — should see 1 quote, $15.6k
4. Click "💳 PAYMENTS" — should see 1 payment recorded
5. Click refresh buttons — data should reload

---

## Recent Changes & Known Issues

### What Changed (Apr 12, 2026)
- **Phase 4 Complete**: AI Lead Extraction + Tradie Follow-up endpoints added
- **Phase 5 Complete**: All integration tests passing
- **Construction MVP**: Full lead → quote → payment workflow ready
- **Fix Applied**: OpenRouter model changed from invalid "mistralai/mistral-7b-instruct:free" to "openrouter/auto"
- **Frontend Updated**: Removed Steve avatar, added construction sections, improved gradient background

### No Known Critical Issues
- Server starts cleanly on port 8000
- All construction endpoints responding correctly
- Dashboard loads all sections
- AI models working with OpenRouter

### Future Enhancements (Post-MVP)
- Add test suite (pytest)
- Implement file upload for job_files table
- Add site_visits note transcription
- Add invoice parsing via document_vision
- Implement Vercel deployment (config ready in vercel.json)

---

## Deployment

### Local Testing
- Runs on `http://127.0.0.1:8000`
- SQLite database (backpocket.db) created automatically
- No external database needed

### Vercel Deployment
- Config file: `vercel.json` (already configured)
- Runtime: Python 3.12 (in runtime.txt)
- Command: `uvicorn main:app --host 0.0.0.0 --port 8000`
- Environment: Set API keys in Vercel dashboard

### GitHub
- Repository: `https://github.com/Sharv619/backpocket-mvp`
- Latest commit: `a552d01` (Construction MVP complete)
- Branch: main (production-ready)

---

## Key Decision Points for Future Work

1. **Data Persistence**: Currently SQLite. For production, consider PostgreSQL + hosted database.
2. **Vector DB**: ChromaDB is in-memory. For scale, use Pinecone or Weaviate.
3. **Task Queue**: No background jobs yet. For async workflows (email sending, PDF generation), add Celery + Redis.
4. **Authentication**: Currently single-user assumption. For multi-user, add user accounts + permissions.
5. **File Storage**: Uploads go to `uploads/`. For production, use AWS S3 or Google Cloud Storage.
6. **Monitoring**: No error tracking yet. Consider Sentry for production.

---

## Git Workflow

```bash
# Branch naming
git checkout -b feature/construction-payments   # New feature
git checkout -b fix/openrouter-model-error     # Bug fix

# Commit style
git commit -m "Add construction features - MVP Phase 4"

# Push to GitHub
git push sharv feature/construction-payments

# Create PR on GitHub (for code review)
```

---

## Questions? Clarifications?

- **Architecture unclear?** Read DETAILED_BUILD_PLAN.md (5-phase breakdown)
- **API reference?** See API_REFERENCE.md (complete endpoint list)
- **Workflows?** See WORKFLOWS.md (business process documentation)
- **Construction details?** See CONSTRUCTION_FEATURES_CHECKLIST.md

---

**Last Updated**: Apr 12, 2026  
**Status**: ✅ MVP Complete (all 5 phases)  
**Ready for**: Local testing, GitHub/Vercel deployment, feature development
