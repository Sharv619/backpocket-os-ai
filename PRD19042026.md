# BackPocket OS — Product Requirements Document

**Version:** 1.0  
**Date:** 2026-04-19  
**Status:** Living Document — MVP Phase Active  
**Owner:** Himanshu Lade  
**Audience:** Engineering, Product, Investors, Contractors

---

## 1. Executive Summary

BackPocket OS is an AI-powered business operating system for small Australian construction and trade businesses ("tradies"). It replaces the chaos of phone calls, paper quotes, and missed Gmail threads with a single intelligent platform that reads emails, extracts leads, generates quotes, sends invoices, tracks payments, and talks back — all via voice or a mobile app.

The target user is a sole-trader or 2–5 person tradie operation making $300k–$2M AUD/year who has zero time for admin and zero tolerance for enterprise software complexity.

**Core value proposition:** "You do the job. BackPocket does the paperwork."

---

## 2. Problem Statement

### Who has this problem

Australian tradies (plumbers, electricians, builders, roofers, tilers, concreters) running small businesses:

- **Lead leakage:** Quotes never sent because the tradie was on a job site and forgot to reply to an email.
- **Invoice lag:** Invoices sent 2–4 weeks late because the owner had to type them manually at night.
- **Compliance risk:** ABNs never validated, GST calculated wrong, ATO audit exposure.
- **Fragmented tools:** Xero for invoicing, WhatsApp for clients, Gmail for leads, a notepad for site visits — no single source of truth.
- **No follow-up:** Sent quotes sit unanswered because nobody has time to chase. Win rate drops.
- **Cash flow crisis:** 30% of receivables are late or uncollected. No automated payment reminders.

### Size of problem

- 1.2M+ registered trade businesses in Australia (ABS 2025)
- Average tradie loses ~$40k/year in unbilled or late-billed work
- 68% have no formal quoting software
- $8.3B addressable market (construction + trade services SaaS in APAC)

---

## 3. Target Users

### Primary Persona — "Steve" (Sole Trader)

- **Who:** Electrician, plumber, or builder operating alone or with 1–2 apprentices
- **Revenue:** $400k–$900k AUD/year
- **Pain:** Spends 3–4 hours/night on admin after being on-site all day
- **Tech comfort:** Uses iPhone, reads WhatsApp, tolerates email, hates spreadsheets
- **Critical need:** Quote in 30 seconds from a voice note, invoice auto-sent on job completion
- **Quote cadence:** 15–30 quotes/month, 40–60% win rate

### Secondary Persona — "Mark" (Small Builder)

- **Who:** Builder with 3–8 subcontractors, $1.5M–$4M revenue
- **Pain:** Subcontractors not followed up, site visits not documented, payments slipping
- **Tech comfort:** Has office admin but wants AI to reduce admin hours
- **Critical need:** Site visit notes → structured scope → auto-quote pipeline

### Out of scope (v1)

- Enterprise construction firms (>20 employees)
- Non-Australian markets (ATO compliance is AU-specific)
- Residential real estate agents
- Retail / hospitality

---

## 4. Product Vision

BackPocket OS is the AI brain a sole trader never had. It:

1. **Listens** — reads Gmail, WhatsApp, voice notes
2. **Thinks** — extracts leads, validates compliance, calculates quotes
3. **Acts** — sends follow-ups, issues invoices, chases payments
4. **Learns** — adapts to each tradie's pricing, tone, and job patterns

**North Star Metric:** Hours of admin per week eliminated per user  
**Target:** From 4 hours/week → under 30 minutes/week

---

## 5. System Architecture

### 5.1 Backend

| Layer | Technology | Notes |
|---|---|---|
| API Server | FastAPI (Python 3.12) | 115+ REST endpoints |
| Database | SQLite (dev) / PostgreSQL (prod) | 38+ tables, auto-switching via `db_router.py` |
| Vector DB | ChromaDB | Semantic search over past decisions |
| AI Models | OpenRouter → Gemini → static fallback | Cost-optimised routing |
| File Processing | PyMuPDF, python-docx, Pillow, fpdf2 | Invoice PDF, document parsing |
| Authentication | Google OAuth 2.0 (Fernet-encrypted tokens) | Gmail + Drive |
| Payments | Stripe SDK | AUD checkout sessions, webhook events |
| Messaging | WHAPI (WhatsApp Business API) | Lead + client communication |
| Deployment | Oracle Cloud ARM (Ampere A1) | 4 vCPU, 24 GB RAM free tier |
| Reverse Proxy | Caddy (auto-HTTPS) | TLS via Let's Encrypt |
| CI/CD | GitHub Actions | test → build-flutter → deploy |

### 5.2 Services Layer (38 Python modules)

```
services/
├── ai/
│   ├── gemini.py          AI model routing (OpenRouter/Gemini)
│   ├── twin_brain.py      Three-twin AI persona system
│   ├── twin_engine.py     Twin orchestration engine
│   ├── agentic_rag.py     ChromaDB retrieval-augmented generation
│   ├── pgvector_rag.py    Postgres pgvector variant
│   └── intent_classifier.py   Voice command intent parsing
├── data/
│   ├── database.py        SQLite schema + CRUD (38 tables)
│   ├── db_router.py       SQLite/Postgres auto-switch
│   ├── postgres_db.py     Postgres-specific operations
│   └── memory.py          Session memory + learned patterns
├── integrations/
│   ├── gmail.py           OAuth 2.0 + email processing
│   ├── drive_integration.py   Google Drive file sync
│   ├── google_sheets.py   Sheets sync for business data
│   ├── whapi.py           WhatsApp Business API
│   └── imap.py            IMAP secondary email
├── business/
│   ├── construction.py    Lead/quote/payment CRUD
│   ├── invoice_engine.py  PDF invoice generation + ABN validation
│   ├── abn_validator.py   ATO checksum algorithm
│   ├── document_vision.py Building material + damage assessment
│   └── document_processor.py  Multi-format document parsing
├── security/
│   ├── crypto.py          Fernet symmetric encryption
│   └── stripe.py          Stripe checkout + webhook verification
└── voice/
    ├── voice_response.py  TTS response generation
    ├── voice_session.py   Voice conversation state
    └── session_manager.py Multi-turn conversation management
```

### 5.3 Mobile App (Flutter)

| Screen | Purpose |
|---|---|
| Dashboard | Business pulse: revenue, open leads, overdue invoices |
| Inbox | Gmail thread triage — approve/reject/draft replies |
| Twin Chat | Conversational AI interface (Pip persona) |
| Documents | Upload invoices, materials photos, site docs |
| Marketing | Generate GBP / Facebook / Instagram posts |
| Instructions | Configure AI behaviour rules |
| Construction | Leads pipeline, quotes, site visits |
| Settings | Server URL, API key, connection test |
| Voice | FAB mic button → voice command overlay |

**Tech stack:** Flutter 3.x, Dart, go_router, provider, SharedPreferences, record (audio), http

### 5.4 AI Twin System

Three specialised AI personas run in parallel:

| Twin | Role | Triggers |
|---|---|---|
| **Accountant Twin** | Analyses financials — margins, cash flow, overdue | Quote creation, payment gaps |
| **Auditor Twin** | Validates data quality — ABN, GST, duplicate leads | Invoice generation, lead ingestion |
| **Admin Twin** | Workflow orchestration — sequences tasks, manages state | Email triage, voice commands |

Each twin has persistent learned patterns in the `session_memory` table. Corrections ("you said X, it should be Y") are written back and improve future responses.

---

## 6. Feature Requirements

### 6.1 Email Triage (Core)

**What it does:** Reads Gmail inbox, extracts actionable items, queues them for one-tap approval.

**Requirements:**
- FR-E1: Connect Gmail via OAuth 2.0. Store refresh token encrypted (Fernet AES-128).
- FR-E2: Poll inbox on configurable schedule (default: every 15 min).
- FR-E3: AI classifies each email: lead / invoice / follow-up-needed / FYI / spam.
- FR-E4: Extract structured data from leads: client name, contact, job type, location, budget, urgency.
- FR-E5: Pending approvals queue — mobile app shows "approve / reject / modify" for each action.
- FR-E6: Draft reply generation with Tradie tone (friendly, direct, no jargon).
- FR-E7: Sender instruction memory — "Always reply to @bigbuild.com.au within 2 hours."
- FR-E8: Search Gmail from mobile (`GET /api/search-gmail`).
- FR-E9: Archive processed emails on approval.

**Acceptance criteria:**
- Email → pending approval within 2 minutes of arrival
- AI classification accuracy ≥ 85% on tradie email corpus
- Draft reply generated in < 4 seconds
- Zero data sent to third parties beyond Google + OpenRouter

---

### 6.2 Lead Management

**What it does:** Auto-creates leads from emails, WhatsApp, or manual entry. Tracks full pipeline.

**Requirements:**
- FR-L1: `POST /api/construction/leads/extract` — AI parses email → creates lead with: client_name, email, phone, job_type, location, suburb, urgency (low/medium/high/critical), estimated_budget, scope_items[].
- FR-L2: Lead statuses: `new → contacted → quoted → accepted → rejected → archived`
- FR-L3: Duplicate detection — same email + job_type within 30 days = flag, not create.
- FR-L4: Lead age alerts — leads older than 48 hours with no action trigger push notification.
- FR-L5: Mobile inbox shows leads sorted by: urgency DESC, then created_at DESC.
- FR-L6: Bulk status update via voice command: "Mark all Sydney plumbing leads as contacted."

**DB schema:**
```sql
leads (
  id INTEGER PRIMARY KEY,
  client_name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  job_type TEXT,
  location TEXT,
  suburb TEXT,
  urgency TEXT CHECK(urgency IN ('low','medium','high','critical')),
  estimated_budget REAL,
  scope_items TEXT,        -- JSON array
  status TEXT DEFAULT 'new',
  source TEXT,             -- 'email' | 'whatsapp' | 'manual' | 'voice'
  notes TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME
)
```

---

### 6.3 Quote Pipeline

**What it does:** Generates itemised quotes with materials + labour. Tracks sent/accepted/rejected.

**Requirements:**
- FR-Q1: `POST /api/construction/quotes` — create quote from lead_id. Auto-calculate: `total = (labor_hours × $150) + materials_cost + (markup_percent / 100 × subtotal)`.
- FR-Q2: Quote PDF generation via `services/invoice_engine.py` — fpdf2, includes: logo, ABN (validated), line items, GST breakdown, bank details, payment terms.
- FR-Q3: Tradie follow-up message — `POST /api/construction/quotes/{id}/tradie-followup` → AI returns 40–60 word friendly message.
- FR-Q4: Quote status flow: `draft → sent → accepted → rejected → invoiced → paid`
- FR-Q5: Quote from voice transcript — `POST /construction/quote-from-transcript` — AI parses spoken scope, returns draft quote.
- FR-Q6: Quote expiry — mark as expired if no response after 14 days.
- FR-Q7: Win rate metric available on dashboard: `accepted / (accepted + rejected)` for last 90 days.

**Pricing formula:**
```
materials_cost  = sum of line items
labor_cost      = hours × hourly_rate (default $150/hr AUD)
subtotal        = materials_cost + labor_cost
markup          = subtotal × markup_percent / 100
gst             = (subtotal + markup) × 0.10
total           = subtotal + markup + gst
```

---

### 6.4 Invoice & Payment Tracking

**What it does:** Auto-generates invoices, records payments, flags overdue.

**Requirements:**
- FR-I1: Invoice PDF auto-generated on quote acceptance. Includes: sequential invoice number, ABN (validated checksum), GST line item, due date (default: 14 days), bank BSB/account.
- FR-I2: ABN validation mandatory before invoice issue — `validate_abn()` must return True or `HTTP 400`.
- FR-I3: GST validation — `validate_gst_amount(subtotal, gst)` within ±1 cent of 10%.
- FR-I4: Payment recording: `POST /api/construction/payments` — client_name, quote_id, amount, received_date.
- FR-I5: Overdue detection — payments past due_date → surface in dashboard "Overdue" card.
- FR-I6: `GET /api/construction/pipeline` — returns: total quotes, revenue in pipeline, draft/sent/accepted counts.

**DB schema (payments):**
```sql
payments (
  id INTEGER PRIMARY KEY,
  quote_id INTEGER REFERENCES quotes(id),
  client_name TEXT,
  amount REAL,
  status TEXT CHECK(status IN ('pending','partial','paid','overdue')),
  due_date DATE,
  received_date DATE,
  notes TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

---

### 6.5 Voice Command Interface

**What it does:** Tradie speaks → AI understands intent → executes action → confirms.

**Requirements:**
- FR-V1: Flutter FAB microphone button → audio recorded via `record` package → sent to `POST /voice/transcribe`.
- FR-V2: Transcription → intent classification → action execution → confirmation card shown.
- FR-V3: Confirmation gate — any destructive action (send email, create quote, mark paid) must show confirmation card with "Yes / Cancel".
- FR-V4: Voice sessions are stateful — multi-turn follow-up ("Change that to high urgency") understood in context.
- FR-V5: Screen context passed with every voice command — AI knows user is on "Construction" screen.
- FR-V6: Supported intents (minimum viable):
  - Navigate to screen
  - Create lead
  - Get quote status
  - Mark payment received
  - Send follow-up message
  - Summarise inbox
  - Search leads by suburb/job type

**Intent classification schema:**
```json
{
  "intent": "create_quote",
  "entities": {
    "client_name": "Dave",
    "job_type": "bathroom reno",
    "estimated_hours": 8,
    "materials_cost": 1200
  },
  "confidence": 0.92,
  "requires_confirmation": true
}
```

---

### 6.6 Document Intelligence

**What it does:** Reads uploaded documents, extracts structured data, assesses building materials.

**Requirements:**
- FR-D1: Upload endpoint accepts: PDF, DOCX, XLSX, PNG, JPG, HEIC.
- FR-D2: Invoice parsing — extract: vendor, total, GST, line items, due date.
- FR-D3: Building material vision — `POST /api/documents/analyze-material?analysis_type=material|damage`
  - Returns: `{material, condition_score (1-10), damage_type, urgency, estimated_repair_hours}`
- FR-D4: Damage assessment — cracks, water ingress, structural concerns identified from photo.
- FR-D5: Results stored in `documents` table and surfaced in Construction → Job Files section.
- FR-D6: `POST /api/drive/sync-to-rag` — sync Google Drive docs into ChromaDB vector store for semantic search.

---

### 6.7 Marketing Content Generation

**What it does:** Generates platform-specific social media posts from job outcomes.

**Requirements:**
- FR-M1: `POST /api/marketing/gbp-post` — Google Business Profile post (150–300 words, SEO-optimised).
- FR-M2: `POST /api/marketing/facebook-post` — Facebook post (80–120 words, casual tradie voice, call-to-action, suburb mention).
- FR-M3: `POST /api/marketing/instagram-caption` — Instagram caption (30–50 words + 5 niche hashtags like `#sydneytiler #bathroomreno`).
- FR-M4: All posts take input: `{job_type, suburb, outcome, before_after: bool}`.
- FR-M5: Posts stored in `marketing_activity` table with `platform` column.
- FR-M6: `GET /api/marketing/insights` — returns last 30 posts + estimated reach metrics.

---

### 6.8 Agentic RAG (Retrieval-Augmented Generation)

**What it does:** Makes the AI smarter over time by learning from past decisions.

**Requirements:**
- FR-R1: Every AI-generated action stored in vector DB with embedding.
- FR-R2: Before any AI response, retrieve top-k similar past decisions.
- FR-R3: Correction ingestion — `POST /api/corrections` → stores "expected vs actual" pair, adjusts future behaviour.
- FR-R4: Pattern confidence scores — high-confidence patterns used as few-shot examples in prompts.
- FR-R5: RAG context passed to AI: "In similar situations, you previously..."
- FR-R6: `POST /api/drive/sync-to-rag` — ingest Google Drive docs into knowledge base.

---

### 6.9 Billing & Subscription

**What it does:** Manages BackPocket's own SaaS subscription billing.

**Requirements:**
- FR-B1: Stripe Checkout Sessions for pilot pricing: $199 AUD/month.
- FR-B2: `POST /api/billing/checkout` → returns Stripe session URL.
- FR-B3: `POST /api/billing/webhook` → verifies Stripe signature, updates subscription status.
- FR-B4: `GET /api/billing/status` → returns: plan, status, next_billing_date.
- FR-B5: Unpaid accounts — API continues to function but nags with in-app banner after 7-day grace.
- FR-B6: `billing_sessions` table tracks all events for audit.

---

### 6.10 Compliance (Australian)

**What it does:** Ensures all financial documents are ATO-compliant.

**Requirements:**
- FR-C1: ABN validation — ATO checksum algorithm (weights: [10,1,3,5,7,9,11,13,15,17,19], mod 89 = 0).
- FR-C2: ABN format display — "XX XXX XXX XXX" on all customer-facing documents.
- FR-C3: GST validation — `|gst - subtotal × 0.10| ≤ $0.01` for all invoices.
- FR-C4: `POST /api/compliance/validate-abn` — public endpoint, returns `{valid: bool, formatted: str}`.
- FR-C5: `POST /api/compliance/validate-gst` — accepts subtotal + gst, returns valid/invalid.
- FR-C6: Invoice PDF includes: ABN, GST registration status, tax invoice header (required by ATO for invoices ≥ $82.50).

---

### 6.11 WhatsApp Integration

**What it does:** Receives client messages via WhatsApp, queues for triage alongside Gmail.

**Requirements:**
- FR-W1: WHAPI webhook receives inbound WhatsApp messages.
- FR-W2: Messages classified same as email: lead / follow-up / payment query / FYI.
- FR-W3: AI-drafted reply sent via `POST /api/whatsapp-test` for approval before sending.
- FR-W4: WhatsApp conversation history stored in `processed_messages` table.
- FR-W5: `GET /api/whatsapp-status` — returns webhook connection status.

---

### 6.12 Kanban / Team Activity Board

**What it does:** Gives visibility into what the AI has done — useful for business review.

**Requirements:**
- FR-K1: `GET /admin/kanban` — serves `kanban.html` static page.
- FR-K2: `GET /admin/api/kanban` — returns JSON with three columns:
  - **Merged This Week** — git commits auto-ingested into `knowledge_notes`
  - **In Progress** — manual notes added by user
  - **Audited** — items older than 7 days
- FR-K3: Business pulse widget — open leads, total quotes, revenue pipeline.
- FR-K4: Leaderboard — commits per author this week.
- FR-K5: `knowledge_notes` seeded from git log on startup if table empty.

---

## 7. API Surface

### 7.1 Base URL

```
Production:  https://app.backpocketsystem.io
Development: http://127.0.0.1:8000
```

### 7.2 Authentication

All endpoints accept optional `X-API-Key` header matching `BP_API_KEY` from `.env`. Current implementation is single-tenant (one user per deployment). Multi-tenant auth is post-MVP.

### 7.3 Endpoint Groups

| Group | Prefix | Count | Purpose |
|---|---|---|---|
| Construction | `/api/construction` | 12 | Leads, quotes, payments, pipeline |
| Voice | `/voice` | 6 | Transcribe, command, session, TTS |
| Email | `/api` | 15 | Inbox, drafts, search, sender rules |
| Documents | `/` | 6 | Upload, analyze, drive sync |
| Marketing | `/api/marketing` | 5 | GBP, FB, IG post generation |
| Admin | `/admin` | 4 | Kanban, DB status, migration |
| Chat | `/api` | 8 | Twin chat, conversation history |
| Instructions | `/api/instructions` | 7 | AI behaviour rules CRUD |
| Billing | `/api/billing` | 3 | Checkout, webhook, status |
| Compliance | `/api/compliance` | 3 | ABN, GST validation |
| Utilities | `/api` | 12 | Hooks, SOPs, workflow, audit |
| Mobile | `/api/mobile` | 4 | Optimised mobile responses |
| Integrations | `/api` | 8 | Sheets, Gmail auth, Drive |
| Webhook | `/webhook` | 3 | WhatsApp, WHAPI events |

**Total: 96+ routed endpoints**

### 7.4 Key Request/Response Contracts

#### Lead Extraction
```
POST /api/construction/leads/extract
Body: { "from": "client@email.com", "subject": "...", "body": "..." }
Response: {
  "lead_id": 42,
  "client_name": "Dave",
  "job_type": "Kitchen reno",
  "location": "Parramatta NSW",
  "urgency": "high",
  "estimated_budget": 15000,
  "scope_items": ["demo old cabinets", "tile splash back", "new benchtop"]
}
```

#### Quote Creation
```
POST /api/construction/quotes
Body: {
  "lead_id": 42,
  "materials_cost": 4800,
  "labor_hours": 16,
  "hourly_rate": 150,
  "markup_percent": 15
}
Response: {
  "quote_id": 7,
  "total_amount": 10120.00,
  "gst": 920.00,
  "pdf_url": "/static/quotes/quote_7.pdf"
}
```

#### Voice Command
```
POST /voice/command
Body: { "text": "Create a quote for Dave's bathroom", "screen": "construction", "tab_index": 6 }
Response: {
  "speech_response": "I've created a draft quote for Dave. Want me to send it?",
  "ui_action": { "navigate_to": "construction" },
  "needs_confirmation": true,
  "follow_up_prompt": "How many hours labour and what materials cost?"
}
```

---

## 8. Database Schema (38 Tables)

### Core Business
| Table | Purpose |
|---|---|
| `leads` | Customer enquiries with job details |
| `quotes` | Itemised quotes with material + labour |
| `payments` | Payment records against quotes |
| `job_files` | Files attached to quotes |
| `site_visits` | On-site notes, materials list, subs |

### Email & Messaging
| Table | Purpose |
|---|---|
| `processed_messages` | All inbound emails/WhatsApp messages |
| `pending_approvals` | Queue of AI actions awaiting approval |
| `corrections` | User corrections → RAG training data |
| `action_history` | Audit log of all AI actions taken |
| `sender_instructions` | Per-sender AI behaviour rules |

### AI & Memory
| Table | Purpose |
|---|---|
| `session_memory` | Conversation state + learned patterns |
| `email_interactions` | Full email → AI response pairs |
| `learned_patterns` | High-confidence behaviour patterns |
| `instructions` | User-configured AI rules |
| `instruction_revisions` | Version history of instructions |

### Integrations
| Table | Purpose |
|---|---|
| `gmail_integration` | OAuth tokens (Fernet-encrypted) |
| `sheets_integration` | Google Sheets sync config |
| `drive_integration` | Google Drive folder config |
| `billing_sessions` | Stripe checkout events |
| `marketing_activity` | Generated social posts (all platforms) |
| `knowledge_notes` | Git commits + manual kanban notes |
| `documents` | Uploaded + parsed document metadata |

---

## 9. Security Requirements

| Requirement | Implementation |
|---|---|
| OAuth token encryption | Fernet AES-128-CBC + HMAC-SHA256 (`services/crypto.py`) |
| Stripe webhook integrity | `stripe.WebhookSignature.verify_header()` |
| ABN validation before invoice | Mandatory checksum gate in `invoice_engine.py` |
| No secrets in code | All keys via `.env` / environment variables |
| API key auth | `X-API-Key` header, configurable via `BP_API_KEY` env |
| HTTPS in production | Caddy auto-TLS via Let's Encrypt |
| SQL injection prevention | Parameterised queries throughout (`?` placeholders) |
| No user PII in logs | Logger filters for email bodies and tokens |

---

## 10. Mobile App Requirements

### Technical
- FR-MOB1: Server URL configurable in Settings — stored in SharedPreferences, no rebuild needed.
- FR-MOB2: Connection test button in Settings — `GET /api/status` within 5-second timeout.
- FR-MOB3: All screens use `SharedPreferences.getString('server_url')` — no hardcoded IPs.
- FR-MOB4: Voice FAB always visible — mic tap → overlay → text input fallback if no mic permission.
- FR-MOB5: Offline-graceful — network errors show snackbar, don't crash.

### UX
- Theme: "5am Warehouse" — dark amber/orange on near-black. Designed for a phone at 5am under site lighting.
- Font: Monospace-adjacent, high contrast.
- Text size: default large (tradies often work with gloves, or phone at arm's length).
- Navigation: Hamburger sidebar (8 sections). No bottom nav bar — too easy to hit accidentally.
- Voice button: Persistent amber FAB bottom-right. Long press = open overlay immediately.

---

## 11. Deployment Architecture

```
GitHub (main branch push)
    ↓ GitHub Actions CI
    ├── pytest (28 tests)
    ├── Flutter web build (--base-href /app/)
    └── SSH deploy to Oracle Cloud ARM
           ├── git pull origin main
           ├── pip install -r requirements.txt
           ├── scp flutter-web → /opt/backpocket/static_flutter
           └── systemctl restart backpocket

Oracle ARM VM (Ampere A1)
    ├── Caddy (port 80/443, auto-TLS)
    │     └── reverse_proxy localhost:8000
    ├── FastAPI + Uvicorn (port 8000, systemd service)
    │     ├── /static        → dashboard HTML
    │     ├── /app           → Flutter web
    │     └── /api/*         → REST API
    └── PostgreSQL (port 5432, local only)

DNS: app.backpocketsystem.io → Oracle public IP
```

**Infrastructure cost:** $0/month (Oracle Cloud Always Free tier, 4 vCPU ARM, 24 GB RAM)

---

## 12. Non-Functional Requirements

| NFR | Target |
|---|---|
| API response time (p95) | < 500ms (non-AI endpoints) |
| AI response time (p95) | < 4 seconds |
| Uptime | 99.5% (single-tenant tolerance) |
| Test coverage | > 40% (currently 28 tests, expanding) |
| Mobile app cold start | < 2 seconds |
| PDF generation | < 1 second |
| Voice transcription latency | < 2 seconds |
| DB query time (p95) | < 50ms |
| Max file upload | 10 MB |

---

## 13. Integrations (External Services)

| Service | Purpose | Auth Method | Cost |
|---|---|---|---|
| Gmail API | Read/send emails | OAuth 2.0 (Fernet-encrypted refresh token) | Free (Google Cloud) |
| Google Drive | File storage, RAG sync | OAuth 2.0 | Free tier |
| Google Sheets | Business data export | OAuth 2.0 | Free tier |
| OpenRouter | AI model routing | API key | ~$0.001–$0.01/request |
| Gemini API | Fallback AI | API key | Pay-per-use |
| Stripe | BackPocket subscription billing | Secret key + webhook | 1.75% + 30c AUD |
| WHAPI | WhatsApp Business | API key | Paid per message |
| Oracle Cloud | Hosting | SSH key | Free (Always Free tier) |
| Cloudflare | DNS + CDN | API token | Free tier |
| ChromaDB | Local vector store | Local (no auth) | Free |

---

## 14. Metrics & Success Criteria

### MVP Success (Day 17 of sprint)

| Metric | Target |
|---|---|
| All 10 sprint chunks shipped | ✅ |
| Test coverage | > 40% |
| OAuth tokens encrypted | ✅ |
| Stripe billing live | ✅ |
| ABN validation live | ✅ |
| Oracle deployment working | ✅ |
| Zero critical security vulnerabilities | ✅ |
| First paying pilot user | 1 |

### Product Success (3 months post-MVP)

| Metric | Target |
|---|---|
| Active paying users | 10 |
| MRR | $1,990 AUD |
| Average admin hours saved per user | > 3 hrs/week |
| Quote-to-invoice conversion | > 60% |
| Lead leakage (leads with no quote sent) | < 5% |
| NPS | > 50 |

### 12-Month Targets

| Metric | Target |
|---|---|
| Active paying users | 100 |
| MRR | $19,900 AUD |
| Churn | < 5%/month |
| Payback period | < 3 months |

---

## 15. Feature Roadmap

### Current (MVP Sprint — April 2026) ✅
- Email triage + lead extraction
- Quote pipeline (create, PDF, send)
- Invoice generation + ABN/GST compliance
- Stripe billing
- OAuth token encryption
- Voice commands (11 intents)
- Building material vision assessment
- Social content generation (GBP, FB, IG)
- Mobile app with dynamic server URL
- Postgres layer + Oracle ARM deployment

### Q2 2026 — Growth Features
- [ ] Automatic payment reminder emails (7-day, 14-day, overdue)
- [ ] Xero integration — push invoices to Xero
- [ ] Subcontractor portal — share job files, get time/materials back
- [ ] iOS push notifications for lead alerts
- [ ] Quote approval link — client clicks link to accept quote (no login)
- [ ] WhatsApp quote delivery — send PDF quote via WhatsApp

### Q3 2026 — Scale Features
- [ ] Multi-tenant accounts (one user per business, multiple businesses)
- [ ] Recurring job templates — tile resealing, annual safety checks
- [ ] Scheduling module — job calendar with travel time (Google Maps API)
- [ ] MYOB integration
- [ ] ATO BAS statement summary (quarterly GST collected)
- [ ] Apprentice/employee time tracking

### Q4 2026 — Enterprise
- [ ] Multi-user per business (owner + admin + apprentice roles)
- [ ] White-label for trade associations
- [ ] Predictive quote pricing (ML model on historical win rates)
- [ ] Insurance certificate tracking
- [ ] Worksite photo progress reports (vision AI)

---

## 16. Known Gaps & Risks

| Gap | Impact | Mitigation |
|---|---|---|
| Single-tenant only (no multi-user) | Can't scale to teams | Post-MVP auth layer |
| ChromaDB in-memory (data lost on restart) | RAG patterns reset | Persist to disk, later Pinecone |
| No automated test for AI quality | Regressions undetected | Eval harness planned Q2 |
| Stripe in test mode | Can't take real money | Live keys before pilot |
| Oracle VM single point of failure | Downtime on reboot | Health check + auto-restart via systemd |
| No rate limiting on AI endpoints | Cost blowout possible | Add per-IP limits post-MVP |
| WhatsApp limited to WHAPI free tier | Message volume cap | Upgrade when volume grows |
| PDF quotes not email-verified | Spoofing risk | Add Docusign-style signature Q2 |
| No mobile push notifications | Lead alerts missed | Firebase Cloud Messaging Q2 |

---

## 17. Glossary

| Term | Definition |
|---|---|
| **Tradie** | Australian colloquial for trade worker (plumber, electrician, builder, etc.) |
| **Twin** | AI persona (Accountant, Auditor, Admin) with specialised prompt + memory |
| **RAG** | Retrieval-Augmented Generation — using vector search to give AI relevant past context |
| **ABN** | Australian Business Number — 11-digit identifier issued by ATO |
| **GST** | Goods and Services Tax — 10% tax on business transactions in Australia |
| **GBP** | Google Business Profile — Google's local business listing |
| **Pip** | BackPocket's AI assistant persona presented in the Twin Chat screen |
| **Scope** | List of work items extracted from a client enquiry |
| **Pipeline** | The full lead → quote → invoice → payment lifecycle |
| **Fernet** | Symmetric encryption scheme (AES-128-CBC + HMAC-SHA256) from Python `cryptography` library |

---

*BackPocket OS PRD v1.0 — Generated 2026-04-19*  
*Next review: 2026-05-19 or after 25 new pilot interviews*
