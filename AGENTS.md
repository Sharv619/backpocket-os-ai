# BackPocket OS - Agent Documentation

## Quick Start

```bash
# Start server
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000

# Dashboard (if root shows API message)
http://127.0.0.1:8000/static/index.html
```

## Key Services

| Service | File | Purpose |
|---------|------|---------|
| API | `main.py` | FastAPI app, all endpoints |
| Database | `services/database.py` | SQLite ops |
| AI | `services/gemini.py` | Gemini API (triage, draft) |
| Documents | `services/document_vision.py` | Moondream/Ollama vision |
| Sheets | `services/google_sheets.py` | Client data sync |
| WhatsApp | `services/whapi.py` | Notifications |

## Database (`backpocket.db`)

Key tables: `pending_approvals`, `instructions`, `sender_instructions`, `sops`, `documents`

## Critical Gotchas

1. **Server restart required** - Changes to `main.py` need restart
2. **Ollama endpoint** - Use `/api/chat` not `/api/generate` for Moondream
3. **Save document bug** - `save_document()` expects bytes, not file object
4. **Dashboard path** - `/static/index.html` not `/`
5. **Gemini model** - Use `gemini-2.5-flash` (not 2.0 - deprecated)

## Mobile API Endpoints (Flutter)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/mobile/pending` | GET | Simplified inbox for mobile (tier_label, preview, age_hours) |
| `/api/mobile/approve` | POST | One-tap approve `{"ref_id": "...", "note": "optional"}` |
| `/api/mobile/chat` | POST | Lightweight twin chat `{"message": "..."}` |

All require `X-API-Key` header when `BP_API_KEY` is set in `.env`.

## Validation Commands

```bash
python3 -c "import main"                       # Test import
curl http://127.0.0.1:8000/api/pending         # Test pending API
curl http://127.0.0.1:8000/api/mobile/pending  # Test mobile API
ruff check .                                    # Lint
./START_DEMO.sh                                 # Full demo reset + start
```

## CHANGE PROTOCOL

Before any change:
1. Read surrounding code (50+ lines)
2. Check for similar patterns in file
3. Test after changes
4. Run `python3 -c "import main"`

## Documents Section (New)

- Upload via `/api/documents/upload`
- Analyze via `/api/documents/analyze/{id}`
- Uses Moondream via Ollama `/api/chat` endpoint
- Frontend: `static/index.html` → Documents → Upload

## Recent Fixes

- Fixed document upload bytes handling
- Fixed Ollama API endpoint (/api/chat)
- Added Documents section with Moondream AI

## Vercel Deployment

- `vercel.json` - Python adapter config
- `runtime.txt` - Python 3.12
- Static files served from `/static/`
- Note: Ollama/Moondream won't work on Vercel (needs local server)