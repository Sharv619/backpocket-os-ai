# BackPocket OS - Agent Documentation

## Quick Start

```bash
# Start MCP servers (all 4 required)
node mcp_servers/leads.mjs &
node mcp_servers/quotes.mjs &
node mcp_servers/pipeline.mjs &
node mcp_servers/knowledge.mjs &

# Start backend
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
# Dashboard: http://127.0.0.1:8000/static/index.html
```

## MCP Servers (4 via .mcp.json)

| Server | File | Tools |
|--------|------|-------|
| `backpocket-leads` | `mcp_servers/leads.mjs` | search_leads, create_lead |
| `backpocket-quotes` | `mcp_servers/quotes.mjs` | create_quote, get_quote_template |
| `backpocket-pipeline` | `mcp_servers/pipeline.mjs` | get_pipeline_summary, record_payment |
| `backpocket-knowledge` | `mcp_servers/knowledge.mjs` | save_note, search_notes |

DO NOT use `src/mcp-wrapper/` — broken (CJS/ESM conflict).

## Key Endpoints

| Endpoint | Purpose |
|-----------|---------|
| `/api/mobile/pending` | Mobile inbox (tier, preview, age_hours) |
| `/api/mobile/approve` | One-tap approve: `{"ref_id": "...", "note": "?"}` |
| `/api/construction/leads` | Lead CRUD |
| `/api/construction/quotes` | Quote CRUD |
| `/api/construction/payments` | Record payment |

## Critical Gotchas

1. **Backend restart** — Changes to `main.py` require restart
2. **Gemini model** — Use `gemini-2.5-flash` (2.0 deprecated)
3. **Port 8000** — Check with `lsof -i:8000` before starting
4. **Dashboard** — Path is `/static/index.html` not `/`

## Flutter Prototype

Location: `flutter_prototype/backpocket_mobile/`

```bash
cd flutter_prototype/backpocket_mobile
flutter pub get
flutter run -d chrome
```

9 screens scaffolded. InboxScreen → `/api/mobile/*`. Other screens need Phase 2 wiring.

## Validation

```bash
python3 -c "import main"                       # Test import
curl http://127.0.0.1:8000/api/mobile/pending # Check API
```

## Architecture

```
FastAPI (main.py)
  └─ services/database.py, gemini.py, document_vision.py

Flutter app → flutter_prototype/backpocket_mobile/
  ├─ lib/models/ (Lead, Quote, Payment, PendingEmail)
  └─ lib/services/api_client.dart

MCP → mcp_servers/*.mjs (4 Node servers)
```

## CHANGE PROTOCOL

Before change: 1) Read 50+ lines 2) Check patterns 3) Test 4) `python3 -c "import main"`