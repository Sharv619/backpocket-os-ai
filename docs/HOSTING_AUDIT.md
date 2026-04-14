# Hosting Tech Stack Audit — Can Vercel Host BackPocket OS?

**Date:** 2026-04-14  
**Status:** ❌ VERCEL NOT SUITABLE

---

## Summary

| Requirement | Current Tech | Vercel Compatible? |
|-------------|--------------|---------------------|
| **Persistent Database** | SQLite (`backpocket.db`) + ChromaDB | ❌ No - ephemeral filesystem |
| **Vector Store (RAG)** | ChromaDB (PersistentClient) | ❌ No - needs persistent disk |
| **PostgreSQL** | Optional (pgvector ready) | ❌ Vercel has no free tier |
| **Ollama (Local AI)** | Self-hosted LLM | ❌ No - needs full server |
| **Background Workers** | Inline only (no queue) | ❌ Limited |
| **Python Server** | FastAPI/uvicorn | ⚠️ Python support limited |

---

## What Vercel Can't Do

### 1. Persistent Storage
- **SQLite** — Vercel's ephemeral FS deletes DB on every deploy/restart
- **ChromaDB** — Vector store needs persistent disk, loses all embeddings on restart
- **Solution:** Needs Oracle ARM / Railway / Render with persistent disk

### 2. Ollama / Local AI
- **Ollama** — Runs Llama 3.2 locally, needs full server (not serverless)
- **Vercel** — Cannot run long-running processes
- **Solution:** Self-host on Oracle ARM (free tier has 24GB RAM!)

### 3. Python Runtime Limits
- **FastAPI** — Works on Vercel but:
  - Cold starts (5-10s delay)
  - No persistent connections
  - Function timeout limits
- **Solution:** Railway/Render/Oracle for backend

---

## Recommended Hosting Stack

### Frontend (Static PWA)
| Platform | Cost | Notes |
|----------|------|-------|
| **Cloudflare Pages** | Free | Best for PWA, global CDN |
| **Netlify** | Free | Alternative |
| **Vercel (static only)** | Free | If just HTML/CSS/JS |

### Backend (FastAPI + SQLite + ChromaDB)
| Platform | Free Tier | Persistent? |
|----------|-----------|--------------|
| **Oracle Cloud ARM** | ✅ 4 OCPU / 24GB RAM | ✅ Yes |
| **Railway** | 500hrs/mo | ✅ Yes |
| **Render** | 750hrs/mo | ✅ Yes |
| **HuggingFace Spaces** | Free | ⚠️ Cold starts |

### Database Options
| Platform | Type | Free Tier |
|----------|------|-----------|
| **Self-host on Oracle** | SQLite/ChromaDB | ✅ Forever |
| **Neon** | PostgreSQL | 0.5GB |
| **Supabase** | PostgreSQL | 500MB |
| **Railway Postgres** | PostgreSQL | 100MB |

---

## ✅ VERDICT: Cannot host on Vercel alone

**Required:** Full server with persistent storage

### Best Free Option: Oracle Cloud Always Free

```
┌─────────────────────────────────────────────┐
│  Oracle Cloud ARM Ampere A1 (Free Forever) │
│  ─────────────────────────────────────────  │
│  • 4 OCPU + 24GB RAM                        │
│  • 200GB Block Storage                      │
│  • Runs: FastAPI + Ollama + SQLite + ChromaDB│
└─────────────────────────────────────────────┘
```

**Alternative:** Railway (easier setup, less generous free tier)

---

## Quick Deploy to Oracle

```bash
# 1. Create Oracle Cloud account → ARM Ampere A1 instance
# 2. SSH in and run:

sudo apt update && sudo apt install -y python3 python3-pip postgresql
curl -fsSL https://ollama.com/install.sh | sh

# 3. Clone and run
git clone https://github.com/Sharv619/backpocket-os-ai.git
cd backpocket-os-ai
pip install -r requirements.txt

# 4. Start
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000

# 5. Cloudflare Tunnel for HTTPS (free)
cloudflared tunnel create backpocket
```

**This gives you persistent memory + local AI for $0 forever.**

---

**Document Owner:** CTO  
**Next Review:** After Oracle ARM provisioning