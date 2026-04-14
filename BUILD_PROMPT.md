# Build Prompt for BackPocket OS

## Project Overview

You are building **BackPocket OS** — an AI-powered System of Record for Australian tradies. The core value proposition is "Pip handles the admin so Steve can run the tools." This is a locally-hosted business management system with voice-to-quote, email automation, lead management, and Google Sheets sync.

## Tech Stack

- **Backend:** FastAPI (Python 3.8+)
- **Database:** SQLite (current), PostgreSQL + PGVector (ready for migration)
- **AI Layer:** Ollama (local Llama 3.2), OpenRouter, Gemini as fallbacks
- **RAG:** ChromaDB (legacy), PGVector (new)
- **Frontend:** Vanilla HTML/JS SPA with PWA support
- **Integrations:** Google Sheets API, Gmail OAuth
- **Hosting:** Cloudflare Pages (frontend), local server with Cloudflare Tunnel (backend)

## Key Files and Their Purposes

### Core Application
- `main.py` — FastAPI application with all routes (4,800+ lines)
- `services/database.py` — SQLite database operations
- `services/gemini.py` — AI router with 3-tier fallback (Ollama → OpenRouter → Gemini)
- `services/agentic_rag.py` — Agentic RAG system for AI responses
- `services/twin_engine.py` — Twin memory system with ChromaDB

### Database Services
- `services/postgres_db.py` — PostgreSQL with Row-Level Security (RLS) - READY FOR MIGRATION
- `services/pgvector_rag.py` — PGVector-based semantic search - READY FOR MIGRATION

### Integrations
- `services/google_sheets.py` — Google Sheets sync ("Business OS" view)
- `services/gmail.py` — Gmail API for email automation

### Frontend
- `static/index.html` — Main dashboard (5,100+ lines)
- `static/kanban.html` — Team contribution tracking board
- `static/manifest.json` — PWA manifest
- `static/sw.js` — Service worker for offline support

### API Endpoints
- `/api/mobile/pending` — Pending approvals (inbox)
- `/api/mobile/approve` — Approve/reject actions
- `/api/voice/quote-from-transcript` — Voice to quote generation
- `/api/voice/transcribe` — Audio transcription
- `/api/construction/leads` — Lead CRUD
- `/api/construction/quotes` — Quote CRUD
- `/api/construction/payments` — Payment recording
- `/api/test-sheets` — Google Sheets connection test

### MCP Servers
- `mcp_servers/leads.mjs` — Lead management MCP
- `mcp_servers/quotes.mjs` — Quote management MCP
- `mcp_servers/pipeline.mjs` — Pipeline operations MCP
- `mcp_servers/knowledge.mjs` — Knowledge bank MCP

### Scripts
- `scripts/sqlite_to_pg_migration.py` — SQLite to PostgreSQL migration
- `scripts/seed_chromadb.py` — Seed ChromaDB with initial data

### Documentation
- `docs/business/WORK_BREAKDOWN_STRUCTURE.md` — Team assignments
- `docs/business/STATUS_UPDATE_2026-04-14.md` — Current status
- `docs/HOSTING_AUDIT.md` — Hosting recommendations
- `docs/business/AI_GOVERNANCE_HANDBOOK.md` — AI rules and compliance

## Features Implemented

### 1. Dashboard
- Pending approvals inbox with tier labels (URGENT, HIGH, MEDIUM, LOW)
- Lead management panel
- Quote pipeline view
- Payment tracking

### 2. Voice-to-Quote
- Accepts transcript text
- Generates structured quote draft
- Returns: job_description, labor_hours, materials_cost, markup_percent, notes

### 3. Email Automation
- AI-generated email drafts
- Human-in-the-loop approval (mandatory)
- Peace of Mind Inbox concept

### 4. Google Sheets Sync
- Logs activities to sheets
- Creates client entries in Master sheet
- Syncs priority lists
- Business OS view for users

### 5. PWA Support
- Manifest with app icons
- Service worker for offline caching
- Mobile-optimized meta tags

### 6. Team Tracking
- Kanban board showing contributions
- Git-based audit logging
- Knowledge bank MCP

## Current Working APIs

Test these to verify the system:

```bash
# Start server
cd /home/lade/Hackathons/.git/backpocket-mvp
source venv/bin/activate
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000

# Test endpoints
curl http://127.0.0.1:8000/api/mobile/pending
curl -X POST http://127.0.0.1:8000/api/voice/quote-from-transcript \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Hi I need a plumber for a leaky tap in the kitchen"}'
```

## What's Ready to Deploy

1. **Frontend** — Already live at https://os.backpocketsystem.io (Cloudflare Pages)
2. **PostgreSQL + PGVector** — Services ready, just needs a PostgreSQL instance
3. **Google Sheets** — Already integrated, just needs OAuth credentials
4. **Voice-to-Quote** — Working API endpoint

## What Needs to Be Done

1. **Deploy Backend** — Connect FastAPI to frontend via Cloudflare Tunnel
2. **Set Up PostgreSQL** — Either local or Oracle Cloud ARM
3. **Configure Google OAuth** — Set up GCP credentials for Sheets/Gmail
4. **Test Full Stack** — End-to-end voice → quote → sheets flow
5. **Oracle Cloud Prep** — If scaling beyond local server capacity

## Build Instructions

### For Local Development:
```bash
# Clone repo
git clone https://github.com/Sharv619/backpocket-os-ai.git
cd backpocket-os-ai

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run backend
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000

# Frontend is in static/ folder - serve with any static server
```

### For Production:
1. Deploy `static/` folder to Cloudflare Pages
2. Deploy backend to server with persistent storage
3. Set up Cloudflare Tunnel for HTTPS access
4. Configure PostgreSQL database
5. Set up Google OAuth credentials

## Important Notes

- **No auto-send** — All AI-generated content requires human approval
- **Local-first** — Data stays on local server, privacy-focused
- **HITL** — Human-in-the-loop is architectural, not optional
- **Compliance** — Follow AI Governance Handbook for any AI features
- **PWA** — Works offline with service worker caching

## Key Concepts to Understand

1. **Twin System** — AI learns from user corrections to improve responses
2. **RAG (Retrieval-Augmented Generation)** — Uses vector database for context
3. **3-Tier AI Fallback** — Local → Cloud 1 → Cloud 2 for reliability
4. **Business OS** — Google Sheets as readable output for non-technical users
5. **PWA** — Progressive Web App installable on mobile devices

---

**Your Task:**

Build, improve, or fix any part of BackPocket OS using this context. Focus on:

1. Making sure the core APIs work correctly
2. Improving the frontend functionality
3. Completing the PostgreSQL migration
4. Testing the Google Sheets integration
5. Adding any missing features from the roadmap

When making changes, always:
- Test with curl before considering it done
- Commit with clear messages
- Update relevant documentation