# BackPocket MVP — Development Workflow

## Daily loop

1. **Pull** — `git pull origin main`
2. **Branch** — `git checkout -b feature/<slug>` or `fix/<slug>`
3. **Run locally** — `python3 -m uvicorn main:app --reload --port 8000`
4. **Test** — `python3 -m pytest tests/ -v`
5. **Commit small** — one logical change per commit
6. **PR** — push, open PR against `main`, request review

## Adding a feature

1. **Schema** — add tables in `services/database.py` + migration script in `scripts/`
2. **Service** — business logic in `services/<name>.py` (pure functions where possible)
3. **Route** — add handler in `routes/<name>.py` (not `main.py` anymore)
4. **Frontend** — section + fetch in `static/index.html`
5. **Tests** — at least one happy-path test in `tests/test_<name>.py`
6. **Docs** — update `CLAUDE.md` if architecture shifts

## Testing

```bash
# Run all
python3 -m pytest tests/ -v

# Run one file
python3 -m pytest tests/test_approve.py -v

# With DEMO_MODE (default in conftest.py)
DEMO_MODE=1 python3 -m pytest tests/
```

- `conftest.py` exposes `app`, `client`, `test_db`, `sample_pending` fixtures
- `DEMO_MODE=1` is set automatically — tests never hit Gmail/OpenRouter

## Refactor discipline (Phase 1–3 in flight)

- Extract duplicated logic to `services/` before adding new callers
- Routes live in `routes/`, not `main.py` — `main.py` only mounts routers + startup
- Global mutable state → `Config` class, injected not imported
- Add type hints as you touch files (start with `services/database.py`)

## Commit style

- Subject ≤ 60 chars, imperative: `add`, `fix`, `refactor`, `test`, `docs`
- Reference phase: `refactor: extract approve.py (Phase 1)`
- Never commit `.env`, `backpocket.db`, `token*.json`

## Deployment

- **Local** — uvicorn on :8000
- **Vercel** — `vercel.json` routes to `main:app`; env vars in dashboard
- Verify `DEMO_MODE` is **unset** in production
