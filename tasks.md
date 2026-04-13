# BackPocket MVP — Tasks

Living task list. Check off as you go. Add new tasks at the bottom of the relevant phase.

---

## Phase 1 — Quick Wins (Morning)

- [ ] Deduplicate approval logic → extract to `services/approve.py`
  - File exists (untracked) — review + finish consolidation
  - Remove duplicate functions from `main.py`
- [ ] Consolidate logging setup in `main.py` (remove duplicate configs)
- [ ] Replace global state with `Config` class
  - Load from env once at startup
  - Inject into routes/services instead of module-level globals

## Phase 2 — Route Extraction (Afternoon)

- [ ] Create `routes/` package structure (`__init__.py`, one file per domain)
- [ ] Extract `pending.py` routes from `main.py`
- [ ] Extract `chat.py` routes (AI twin chat endpoints)
- [ ] Extract `whatsapp.py` webhook handler
- [ ] Extract `construction.py` routes (leads, quotes, payments)
- [ ] Refactor `main.py` to only: app init, router mounts, startup hooks
  - Target: `main.py` under 300 lines (currently 4300+)

## Phase 3 — Tests + Types (Evening)

- [x] Create `tests/` with `conftest.py`
- [x] Add basic approve.py test coverage (3 tests passing)
- [ ] Add pytest to `requirements.txt` (or `requirements-dev.txt`)
- [ ] Add route-level tests using `TestClient` fixture
  - `test_construction_routes.py` — leads/quotes/payments CRUD
  - `test_chat_routes.py` — twin chat smoke tests
- [ ] Add type hints to `services/database.py`
- [ ] Add type hints to `services/construction.py`
- [ ] Run `mypy services/` and fix top errors

---

## Backlog (post-refactor)

- [ ] Replace SQLite with Postgres for production
- [ ] Swap ChromaDB → Pinecone/Weaviate for scale
- [ ] Add Celery + Redis for background jobs (email send, PDF gen)
- [ ] Multi-user auth (currently single-user assumption)
- [ ] S3/GCS for `uploads/` in production
- [ ] Sentry error tracking
- [ ] File upload endpoint for `job_files` table
- [ ] Site visit transcription → `site_visits` table
- [ ] Invoice parsing via `document_vision`

## Done

- [x] MVP Phase 4 — AI Lead Extraction + Tradie Follow-up
- [x] MVP Phase 5 — Integration tests passing
- [x] OpenRouter model fix (`openrouter/auto`)
- [x] Frontend construction sections + gradient
- [x] Vercel deploy config
- [x] Flutter mobile prototype scaffolding
