# Flutter Migration Plan

**Date**: 2026-04-13
**Status**: Plan — not yet executing
**Decision**: Move frontend from `static/index.html` (5,100 lines, vanilla JS) to the existing Flutter prototype in `flutter_prototype/backpocket_mobile/`.

---

## Why Flutter

1. **One codebase, three targets**: iOS, Android, Web (desktop dashboard parity).
2. **The prototype already exists** — 1,682 lines in `main.dart`, 8 screens scaffolded, real API calls to `/api/mobile/*` already working.
3. **Tradies are mobile-first**. A plumber on the road needs an app, not a web dashboard.
4. **The current HTML is a single-page div toggler** — no routing, no deep links, hard to extend. A tab rewrite would be large work anyway.

## Non-goals

- Not replacing the FastAPI backend. All data calls stay against the current Python server.
- Not migrating `/admin/kanban` on day one — internal team dashboard stays web-only until Flutter Web parity is proved.
- Not rewriting the AI/MCP layer (already Flutter-agnostic).

## Current State Audit

### Existing Flutter prototype (`flutter_prototype/backpocket_mobile/`)

- `lib/main.dart` — 1,682 lines
- `lib/theme.dart` — 285 lines
- `pubspec.yaml` — Flutter SDK `^3.11.1`, deps: `http`, `shared_preferences`, `intl`, `camera`, `google_fonts`, `provider`
- `TwinController extends ChangeNotifier` — state management in place
- 8 screens scaffolded in AppShell: Dashboard, Inbox, TwinChat, Documents, Marketing, Instructions, Construction, Settings, + VisionChat

### HTML → Flutter screen mapping

| HTML section | Flutter screen | Status |
|---|---|---|
| `construction-leads-section` | `ConstructionScreen` — leads tab | Scaffolded, needs API wiring |
| `construction-pipeline-section` | `ConstructionScreen` — pipeline tab | Scaffolded |
| `construction-payments-section` | `ConstructionScreen` — payments tab | Scaffolded |
| `email` | `InboxScreen` | Wired to `/api/mobile/pending` + `/api/mobile/approve` ✅ |
| `docs` (document tab — currently broken) | `DocumentsScreen` | Scaffolded, needs fix |
| `marketing` | `MarketingScreen` | Scaffolded |
| `tasks` | `InstructionsScreen` | Scaffolded |
| Twin chat | `TwinChatScreen` | Scaffolded |
| Invoice/vision upload | `VisionChatScreen` | Scaffolded |
| *(new)* `/admin/kanban` | **KanbanScreen** | Build from scratch |

## Architecture

```
┌─ Flutter app (iOS + Android + Web)
│  ├─ lib/main.dart                  ← shell, bottom nav, routing
│  ├─ lib/screens/                   ← one file per screen (extract from main.dart)
│  │    ├─ dashboard_screen.dart
│  │    ├─ inbox_screen.dart
│  │    ├─ documents_screen.dart
│  │    ├─ construction_screen.dart
│  │    ├─ marketing_screen.dart
│  │    ├─ tasks_screen.dart
│  │    ├─ kanban_screen.dart        ← NEW
│  │    ├─ twin_chat_screen.dart
│  │    └─ settings_screen.dart
│  ├─ lib/services/api_client.dart   ← wraps all /api/* calls, one http instance
│  ├─ lib/models/                    ← Lead, Quote, Payment, Note dataclasses
│  └─ lib/theme.dart
│
└─ FastAPI backend (unchanged)
     /api/construction/*       — already exists
     /api/mobile/*             — already exists
     /admin/api/kanban         — already exists
     /api/docs/*               — may need adding for document tab fix
```

**Routing**: adopt `go_router` for real URLs (`/leads`, `/quotes/42`, `/kanban`). Fixes the "everything opens in a div" issue — each screen gets its own URL, deep-linkable, back-button works.

**State**: keep `provider` (already in deps). One `TwinController` at app root, one `ApiClient` singleton.

**Auth**: Flutter stores `server_url` and `api_key` in `shared_preferences` (prototype already does this). No new auth work.

## Phased Plan

### Phase 0 — Verify prototype runs (0.5 day)

- `cd flutter_prototype/backpocket_mobile && flutter pub get && flutter run -d chrome`
- Point it at `http://127.0.0.1:8000` — confirm InboxScreen pulls real data
- Catalogue broken screens (screenshots into `docs/flutter_audit/`)

### Phase 1 — Refactor monolith (1 day)

- Split `main.dart` (1,682 lines) into one file per screen under `lib/screens/`
- Extract all `http.get/post` into `lib/services/api_client.dart`
- Add `go_router`, convert bottom-nav to routed URLs
- Why first: every subsequent phase gets easier once the monolith is split. Do this before adding features.

### Phase 2 — Port working HTML features (3–4 days)

For each of these, read the HTML section → implement Flutter equivalent → delete HTML section once Flutter version is verified:

1. **Construction leads** (`/api/construction/leads`) — list, detail, create
2. **Construction quotes** (`/api/construction/quotes`) — list, detail, create with calculator
3. **Construction payments** (`/api/construction/payments`) — list, record payment
4. **Documents tab fix** — this is the one you flagged as broken. Investigate HTML workflow first, mirror fixed version in Flutter (don't port the bug).
5. **Email / Inbox** — already mostly working, polish
6. **Twin chat** — already scaffolded, wire to `/api/chat`

### Phase 3 — New screens (1–2 days)

- **KanbanScreen** — port `/admin/kanban` dashboard. Mobile-friendly layout (columns stack on narrow screens).
- **Site visit** — camera integration for on-site photos (deps already installed).

### Phase 4 — Retire HTML (0.5 day)

- Keep `/admin/kanban` web page alive (useful on desktop for boss view).
- Redirect `/` → Flutter web build (`static/index.html` replaced with Flutter's `index.html` from `build/web`).
- Archive old HTML sections under `static/_archive_html/` for reference.

### Phase 5 — Mobile builds (1 day)

- Android: `flutter build apk` → sideload to tradie's phone for testing
- iOS: requires Apple Developer account; skip until there's budget for it
- Web: `flutter build web` → serve from FastAPI as `/app`

**Total: ~7 days of focused work.** Ship incrementally — each phase leaves a working system.

## Backend Changes Needed

Small, additive — no breaking changes.

- `/api/docs/*` endpoints (for documents tab) — check what the HTML currently calls, expose as JSON API
- CORS: add `http://localhost` origins to FastAPI for Flutter web dev
- Possibly `/api/mobile/kanban` — alias of `/admin/api/kanban` for clarity

## Risks & Tradeoffs

| Risk | Mitigation |
|------|-----------|
| **Non-technical teammates (marketing, law, research) can't edit Flutter** | They edit content via `save_note` + markdown in the knowledge bank, not code. Devs own Flutter. |
| **Flutter Web bundle size + SEO** | `/admin/kanban` stays as plain HTML for boss/desktop. Flutter Web only for authed team app. |
| **Prototype is 5 months old, deps may drift** | Phase 0 validates this before committing further effort. Escape hatch: if pub get fails hard, re-scaffold with current Flutter stable. |
| **Splitting main.dart could introduce bugs** | Do Phase 1 refactor behind commits per screen — easy git bisect if anything breaks. |
| **"HTML vanilla JS works today" risk of regression** | Keep HTML alive until each Flutter screen is verified. Delete HTML sections one-by-one, not in a big bang. |

## Open Decisions for Sharv

- [ ] Approve phased approach above, or want to compress (risky)?
- [ ] Android-only first, or iOS from day one (needs Apple Dev account $99/yr)?
- [ ] Flutter Web — serve at `/app` on existing FastAPI, or standalone on Vercel?
- [ ] Keep `/admin/kanban` as plain HTML permanently, or also port to Flutter Web eventually?

## Immediate next steps (if approved)

1. I run `flutter pub get` + `flutter run -d chrome` in the prototype to confirm it boots
2. I report back with a screenshot / list of broken screens
3. You approve Phase 1 (the refactor), then we go
