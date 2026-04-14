# BackPocket OS — 17-Day Sprint WBS
## April 13–30, 2026 | Target: 3 Paying Customers

---

## Sprint Overview

| Metric | Value |
|--------|-------|
| **Start** | Apr 13, 2026 |
| **End** | Apr 30, 2026 |
| **Days** | 17 |
| **Target Customers** | 3 paid |
| **Target Env** | Oracle Cloud ARM (Always Free) |

---

## Tracks & EPICs

### Track 1: Revenue Features (P0)
- **EPIC B**: Voice-to-Quote
- **EPIC C**: Billing + Polish

### Track 2: Infrastructure & Multi-tenant (P0)
- **EPIC A**: Foundation (Oracle ARM + CI/CD)
- **EPIC E**: Data Layer Hardening (Postgres)
- **EPIC F**: Multi-Tenant Auth + RLS
- **EPIC G**: Photo-to-Post
- **EPIC H**: Security Hardening

---

## WBS Structure

```
EPIC A — Foundation (Days 1–3)
├── A1. Oracle ARM provisioning script
├── A2. GitHub Actions deploy workflow  
├── A3. Auth IdP ADR (Supabase vs Clerk)
└── A4. Backup to R2 script

EPIC B — Voice-to-Quote (Days 4–7)
├── B1. Flutter voice capture UI
├── B2. /api/voice/transcribe endpoint
├── B3. /api/voice/quote-from-transcript endpoint
├── B4. Flutter quote review UI
└── B5. Prompt engineering for Trinity

EPIC C — Billing (Days 8–12)
├── C1. Stripe integration (main.py)
├── C2. Flutter billing UI
└── C3. WhatsApp nudge logic

EPIC E — Data Layer (Days 1–7)
├── E1. SQLite to Postgres migration script
├── E2. services/postgres_db.py (SQLAlchemy)
├── E3. services/pgvector_rag.py
└── E4. Dual-write logic

EPIC F — Auth + RLS (Days 4–10)
├── F1. IdP integration code
├── F2. RLS policies
├── F3. Token encryption
└── F4. Caddy security headers

EPIC G — Photo-to-Post (Days 8–13)
├── G1. Flutter camera UI
├── G2. /api/vision/analyze_materials endpoint
├── G3. /api/social/generate_post endpoint
└── G4. Flutter social post review UI

EPIC H — Security (Days 11–17)
├── H1. Privacy policy / TOS drafts
├── H2. OWASP ZAP automation
└── H3. CIS benchmark hardening
```

---

## Dependencies

```
A1 ──────► A2
 │           │
 └───────────┴─────────────► E1 ──► E2 ──► E3 ──► F2
                │              │              │
                ▼              ▼              ▼
               B1 ──► B2 ──► B3 ◄───► G1 ◄───► G2
               │              │              │
               └──────────────┴──────────────┴───────► C1
```

---

## Daily Allocation

| Day | Date | Focus | Owner |
|-----|------|-------|-------|
| 1 | Apr 13 | Oracle ARM + A1 | IT Engineer |
| 2 | Apr 14 | A2 + A3 | IT Engineer |
| 3 | Apr 15 | A4 + E1 start | IT Engineer |
| 4 | Apr 16 | B1 + B2 | Minimax |
| 5 | Apr 17 | F1 + E2 | IT Engineer |
| 6 | Apr 18 | B3 + B4 | Minimax |
| 7 | Apr 19 | B5 + G1 | Minimax |
| 8 | Apr 20 | C1 + G2 | Joint |
| 9 | Apr 21 | C2 + G3 | Minimax |
| 10 | Apr 22 | F2 + F3 | IT Engineer |
| 11 | Apr 23 | E3 + E4 | IT Engineer |
| 12 | Apr 24 | C3 + polish | Minimax |
| 13 | Apr 25 | G4 + integration | Minimax |
| 14 | Apr 26 | H1 + H2 | IT Engineer |
| 15 | Apr 27 | H3 + pen-test prep | IT Engineer |
| 16 | Apr 28 | Integration test + fixes | Joint |
| 17 | Apr 29 | Go-live prep | IT Engineer |
| 18 | Apr 30 | **3 CUSTOMERS** | Founder |

---

## Success Metrics

| Metric | Target | Measure |
|--------|--------|---------|
| Paid customers | 3 | Stripe webhooks |
| Uptime | 99.9% | Oracle status |
| Voice-to-Quote | <60s | End-to-end timing |
| Photo-to-Post | <30s | End-to-end timing |
| RLS | Active | Postgres policies |