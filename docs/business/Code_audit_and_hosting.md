# Code Audit & Hosting Strategy

**Owner:** Fractional CTO  
**Status:** Hackathon build → Production hardening  
**Date:** 2026-04-13

---

## 1. Deep Audit — Current System

### Topology
┌──────────────────────┐ ┌──────────────────────────┐
│ Browser / Flutter │◄──────►│ FastAPI (main.py) │
│ static/index.html │ HTTP │ - Local Server │
└──────────────────────┘ └───────────┬──────────┘
│
▼
┌──────────────────┐
│ AI Layer │
│ (services/) │
│ - Ollama (local) │
│ - OpenRouter │
│ - Gemini native │
│ - ChromaDB (RAG) │
└──────────────────┘
### Core Connections (What's Working)

| Layer | Component | File | Notes for Demo Day |
|-------|-----------|------|--------------------|
| **API** | FastAPI + Uvicorn | `main.py` | Single Python server, handles all requests. |
| **Data** | SQLite | `backpocket.db` | Local, persistent database for demo data. |
| **AI Router** | 3-tier fallback | `services/gemini.py` | Local AI → Ollama → OpenRouter → Gemini native. **Hardened with fallbacks.** |
| **RAG** | ChromaDB (in-process) | `services/agentic_rag.py` | Vector store of past decisions/corrections. |
| **Frontend** | Vanilla HTML/JS | `static/index.html` | Dashboard with simulated Voice-to-Invoice, seeded emails. |

---

## 2. Pain Points (As of Hackathon Demo)

| # | Pain Point | Mitigation for Demo | Post-Hackathon Plan (WBS) |
|---|-----------|---------------------|--------------------------|
| 1 | **Monolithic `main.py`** | All critical endpoints isolated and stable. | Route extraction is Epic A (Week 1) |
| 2 | **SQLite concurrency** | Only single user for demo; local-only. | Postgres migration is Epic E (Track 2) |
| 3 | **No multi-tenant auth** | Single user ("Steve") for demo. | Multi-tenant Auth/RLS is Epic F (Track 2) |
| 4 | **OAuth tokens on disk** | Gitignored, no actual tokens in repo. | Encrypt + move to DB is Epic F (Track 2) |
| 5 | **ChromaDB non-persistent** | Works for fresh demo; re-seeded on restart. | Persistent volume / `pgvector` is Epic E (Track 2) |

---

## 3. Next Coding Steps (Post-Hackathon → Production)

**Our 17-day sprint starts now (see `PROJECT_WBS.md`).**

*   **Foundation:** Oracle ARM VM provisioning, Cloudflare Tunnel, Caddy, GitHub Actions CI/CD.
*   **Data Layer Hardening:** Migrate SQLite → Postgres, persistent ChromaDB (`pgvector`).
*   **Authentication & Security:** Multi-tenant Auth (Supabase/Clerk), Row-Level Security (RLS), encrypted secrets, robust security headers, rate limiting.
*   **Core Features:** Voice-to-Quote E2E (Flutter + Whisper), Photo-to-Post (social media integration).
*   **Compliance:** ATO, APP, GDPR adherence.
*   **Observability:** Sentry error tracking, uptime monitoring.

---

## 4. Free / Open-Source Hosting Architecture (for Judges)

**Goal:** Ship production on $0 infrastructure while preserving the "local-first" moat.

### Recommended Topology
┌──────────────────────────┐
│  Vercel (Frontend)       │
|Customer Browser ────────►│ static/index.html │ [Free: Hobby tier]
│ Flutter Web build │
└────────────┬─────────────┘
│ HTTPS
▼
┌──────────────────────────┐
│ Cloudflare Tunnel │ [Free]
│ (zero-trust ingress) │
└────────────┬─────────────┘
│
▼
┌────────────────────────────────────────────┐
│ Oracle Cloud Always Free — ARM Ampere A1 │
│ 4 OCPU / 24 GB RAM / 200 GB block storage │
│ ───────────────────────────────────────── │
│ • FastAPI (uvicorn) │
│ • Ollama (Llama 3.2, Gemma) — LOCAL AI │
│ • Postgres 16 (self-hosted) │
│ • ChromaDB (persistent volume) │
│ • Caddy (reverse proxy + auto-TLS) │
└────────────────────────────────────────────┘
│
▼
┌──────────────────────────┐
│ GitHub Actions (CI/CD) │ [Free: 2000 min/mo]
│ Sentry (errors) │ [Free: 5k events/mo]
│ UptimeRobot (monitor) │ [Free: 50 monitors]
└──────────────────────────┘
                         
### Why This Stack (Key Talking Points)

*   **Oracle Cloud ARM "Always Free":** 24 GB RAM runs Ollama **for free**, cutting cloud AI costs. 4 OCPUs for users. 200 GB storage for Postgres + ChromaDB. This is your **$0 infra to 500 users** pitch.
*   **Vercel + Cloudflare Tunnel:** Free, fast frontend delivery globally, with secure "zero-trust" access to the backend, **no open ports**.
*   **Postgres + Ollama Self-Hosted:** Keeps data in our control, reinforcing the "local-first, System of Record" moat.
*   **GitHub Actions + Sentry:** Professional development + monitoring, all free.

**This is how we maintain 85%+ gross margins at scale, while keeping Steve's data private.**

    