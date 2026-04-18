# Code Audit & Hosting Strategy

**Owner:** Fractional CTO  
**Status:** Hackathon build → Production hardening  
**Date:** 2026-04-13

---

## 1. Deep Audit — Current System

### Topology

```
 ┌──────────────────────┐        ┌──────────────────────────────┐
 │  Browser / Flutter   │◄──────►│   FastAPI (main.py, 4,821 LOC)│
 │  static/index.html   │  HTTP  │   - routes/chat.py            │
 │  backpocket_mobile/  │        │   - routes/pending.py         │
 └──────────────────────┘        │   - 50+ inline handlers       │
                                 └───────────┬──────────────────┘
                                             │
         ┌───────────────────────────────────┼──────────────────────────────┐
         ▼                                   ▼                              ▼
 ┌───────────────┐                 ┌──────────────────┐            ┌────────────────┐
 │ SQLite        │                 │ AI Layer         │            │ Google APIs    │
 │ backpocket.db │                 │ (services/)      │            │ Gmail / Drive  │
 │ 22+ tables    │                 │ - Ollama (local) │            │ Sheets / Maps  │
 │ single file   │                 │ - OpenRouter     │            │ OAuth 2.0      │
 └───────────────┘                 │ - Gemini native  │            └────────────────┘
                                   │ - ChromaDB (RAG) │
                                   └──────────────────┘
```

### Core Connections

| Layer | Component | File | Notes |
|-------|-----------|------|-------|
| **API** | FastAPI + Uvicorn | `main.py` (4,821 lines) | Monolith; route extraction in progress (`routes/chat.py`, `routes/pending.py`) |
| **Data** | SQLite, WAL default | `services/database.py`, `backpocket.db` | 22+ tables: `pending_approvals`, `leads`, `quotes`, `payments`, `corrections`, `session_memory`, etc. |
| **AI Router** | 3-tier fallback | `services/gemini.py` | Local AI server → Ollama → OpenRouter → Gemini native. Graceful degradation verified. |
| **RAG** | ChromaDB (in-process) | `services/agentic_rag.py` | Vector store of past decisions/corrections. Not persisted across redeploys. |
| **Integrations** | Google Workspace | `services/gmail.py`, `google_sheets.py`, `drive_integration.py` | OAuth refresh tokens stored in `token.json` (file-based). |
| **Orchestration** | Model Context Protocol | `src/mcp-wrapper/`, `.mcp.json` | 4 MCP servers, 13 custom tradie tools. |
| **Mobile** | Flutter prototype | `flutter_prototype/backpocket_mobile/` | On-device embeddings + local agent (the "System of Record" moat). |
| **Frontend Web** | Vanilla HTML/JS SPA | `static/index.html` | No build step. Fetches `/api/construction/*`. |
| **Deploy** | Vercel (serverless Python) | `vercel.json` | Currently configured; SQLite on Vercel is ephemeral (blocker for prod). |

### Auth & Identity

- Gmail OAuth 2.0 refresh tokens in `token.json` on disk.
- **No application-level user accounts.** The backend assumes single-tenant ("Steve").
- Multi-user requires a full auth stack (see Epic B in `PROJECT_WBS.md`).

---

## 2. Pain Points (Technical Bottlenecks)

| # | Pain Point | Severity | Why It Blocks Scale |
|---|-----------|----------|---------------------|
| 1 | **`main.py` is a 4,821-line monolith** | High | Cognitive load; merge conflicts; slow reviews. Route extraction to `routes/` is 2/N complete. |
| 2 | **SQLite concurrency ceiling** | **Critical** | Single writer; file-locked. Breaks the moment we exceed 1 paid user writing to the same file. Vercel serverless = ephemeral FS = data loss. |
| 3 | **No multi-tenant auth** | **Critical** | Cannot sell a SaaS subscription without user accounts, row-level isolation, and billing identity. |
| 4 | **OAuth tokens on disk (`token.json`)** | High | Not safe for multi-user; tokens must live in DB, encrypted at rest (per-user). |
| 5 | **ChromaDB in-process, non-persistent** | Medium | RAG memory resets on restart. Needs managed vector store or persistent volume. |
| 6 | **No background job queue** | Medium | Long-running AI drafts block the request thread. Email polling runs inline. |
| 7 | **No structured logging / observability** | Medium | `logger.info` only. No Sentry, no metrics, no trace IDs. Demo-debuggable, not prod-debuggable. |
| 8 | **Secrets in `.env` + committed `.bat` launchers** | High | Ops surface leaks; need Vault/Doppler or at minimum provider-managed secrets. |
| 9 | **No automated test coverage of HTTP routes** | Medium | `tests/test_approve.py` covers 3 pure functions. Regression risk on every refactor. |
| 10 | **Frontend has no build step** | Low (by design for hackathon) | Fine for MVP; Flutter mobile is the real future client. |

---

## 3. Next Coding Steps (Post-Hackathon → Production)

**Sequenced, 90-day horizon.** Maps 1:1 to `PROJECT_WBS.md`.

### Week 1–2 — Kill the monolith
- Finish route extraction: `routes/construction.py`, `routes/whatsapp.py`, `routes/integrations.py`.
- Target: `main.py` < 300 lines (mount routers + startup only).
- Introduce a `Config` dataclass loaded from env; delete module-level globals.

### Week 3–5 — Data layer migration
- Migrate `backpocket.db` → Postgres (managed: Neon, Supabase free tier, or self-host on Oracle).
- Add SQLAlchemy + Alembic. Preserve SQLite for local dev only.
- Move ChromaDB to persistent volume, or swap to `pgvector`.

### Week 6–8 — AuthN/AuthZ
- Supabase Auth (Google SSO) or Clerk for user identity.
- Add `user_id` to every tenant-scoped table; enforce Row Level Security.
- Encrypt Google refresh tokens (Fernet) keyed per-user.

### Week 9–10 — Core features ("Pip" for "Steve")
- **Voice-to-Quote**: Flutter voice capture → Whisper (local) → structured quote draft.
- **Photo-to-Post**: Before/after image → `services/document_vision.py` → caption → social draft.
- Both features land behind the existing human-in-the-loop approval screen.

### Week 11–12 — Observability + Launch
- Sentry + OpenTelemetry traces.
- Billing (Stripe): $299 one-off + $15/mo recurring.
- Smoke-test suite: pytest + FastAPI TestClient, 80%+ route coverage.

---

## 4. Free / Open-Source Hosting Architecture

**Goal:** ship production on $0 infrastructure while preserving the "local-first" moat.

### Recommended Topology

```
                             ┌──────────────────────────┐
                             │  Vercel (Frontend)       │
  Customer Browser ─────────►│  static/index.html       │  [Free: Hobby tier]
                             │  Flutter Web build       │
                             └────────────┬─────────────┘
                                          │ HTTPS
                                          ▼
                             ┌──────────────────────────┐
                             │  Cloudflare Tunnel       │  [Free]
                             │  (zero-trust, no open    │
                             │  inbound ports)          │
                             └────────────┬─────────────┘
                                          │
                                          ▼
                    ┌────────────────────────────────────────────┐
                    │  Oracle Cloud Always Free — ARM Ampere A1  │
                    │  4 OCPU / 24 GB RAM / 200 GB block storage │
                    │  ─────────────────────────────────────────  │
                    │  • FastAPI (uvicorn, systemd)              │
                    │  • Ollama (Llama 3.2, Gemma) — LOCAL AI    │
                    │  • Postgres 16 (self-hosted)               │
                    │  • ChromaDB (persistent volume)            │
                    │  • Caddy (reverse proxy + auto-TLS)        │
                    └────────────────────────────────────────────┘
                                          │
                                          ▼
                             ┌──────────────────────────┐
                             │  GitHub Actions (CI/CD)  │  [Free: 2000 min/mo]
                             │  Sentry (errors)         │  [Free: 5k events/mo]
                             │  UptimeRobot (monitor)   │  [Free: 50 monitors]
                             └──────────────────────────┘
```

### Why This Stack

| Choice | Cost | Why It Wins |
|--------|------|------------|
| **Oracle Cloud ARM "Always Free"** | $0 forever | 24 GB RAM → runs Ollama (Llama 3.2 3B or Gemma 2B) **for free**, eliminating OpenRouter spend on common paths. 4 OCPUs handle concurrent users. 200 GB block storage hosts Postgres + ChromaDB. |
| **Vercel Hobby** | $0 | Global edge for the static frontend + Flutter web. No cold start for users. |
| **Cloudflare Tunnel** | $0 | Oracle VM has **no open inbound ports**. Tunnel punches out to Cloudflare; traffic enters via CF only. Zero-trust posture by default. |
| **Postgres self-hosted** | $0 | Owned by us. Matches the "System of Record, local-first" positioning. Alternative: Supabase/Neon free tier if we want managed. |
| **Caddy** | $0 | Automatic Let's Encrypt TLS. One-line config. |
| **GitHub Actions** | $0 | CI runs tests + deploys to Oracle via SSH. |
| **Sentry Developer** | $0 | Error tracking; 5k events/mo is plenty pre-launch. |

### Deployment Flow

```bash
# 1. Provision Oracle ARM instance (one-time, ~10 min)
# 2. Install stack
sudo apt install -y postgresql caddy
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b gemma2:2b

# 3. Clone + run
git clone github.com/Sharv619/backpocket-mvp
systemctl enable --now backpocket    # uvicorn via systemd unit

# 4. Cloudflare Tunnel (one command)
cloudflared tunnel create backpocket
cloudflared tunnel route dns backpocket api.backpocket.ai

# 5. CI deploys on push-to-main
```

### Cost Projection

| Users | Monthly Cost | Notes |
|-------|-------------|-------|
| 0 – 500 | **$0** | Oracle Always Free ceiling holds |
| 500 – 2,000 | ~$40/mo | Upgrade: Oracle paid VM (4 OCPU, 48 GB) |
| 2,000 – 5,000 | ~$200/mo | Add managed Postgres (Neon Pro) + CDN bandwidth |

At **5,000 users × $15/mo = $75k/mo revenue**, infra is rounding error → 85%+ gross margin holds.

### Why Not AWS/GCP/Azure

- Spin-up cost on a hackathon timeline = lost week.
- Free tiers expire at 12 months; Oracle's is **perpetual**.
- Egress fees on AWS kill margin at scale; Oracle Always Free includes 10 TB/mo egress.
