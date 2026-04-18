# Tasks — BackPocket MVP

> Active task tracker. Ordered by focus chain priority.
> Last updated: 2026-04-18

---

## Recently Completed

- [x] **Backend refactor**: Split main.py 4229 → 213 lines (14 route modules)
- [x] **Flutter refactor**: Split main.dart 1756 → 521 lines (extracted TwinChatScreen)
- [x] **Pydantic models**: Consolidated into `app/models/schemas.py`
- [x] **Background services**: Extracted to `services/background.py`
- [x] **Webhook handler**: Extracted to `routes/webhook.py`
- [x] **Voice command system**: Intent classifier + session state machine + handlers (50+ intents)
- [x] **Voice UI widgets**: VoiceFab, VoiceRecordingOverlay, VoiceConfirmationCard
- [x] **AI workflow doc**: `docs/business/aiworkflow.md` — full intent taxonomy
- [x] **Focus chain plan**: `docs/focus_chain.md` — 7 focus chains, prioritized

---

## P0 — Core Business Value

### FC-1: Construction Pipeline Stage Tracker
- [ ] Add `workflow_stage` INT column to `leads` table in `services/database.py`
- [ ] Create `PATCH /api/construction/leads/{id}/stage` endpoint in `routes/construction.py`
- [ ] Implement auto-advance rules in `services/construction.py` (quote sent → stage 5, etc.)
- [ ] Build `widgets/workflow_stage_tracker.dart` — horizontal stepper with branch at stage 6
- [ ] Integrate stage tracker into lead detail view in `construction_screen.dart`
- [ ] Add pipeline stage summary to `dashboard_screen.dart`

### FC-2: Lead → Quote → Invoice Pipeline UI
- [ ] "Create Quote" button on lead detail → pre-fill from lead data
- [ ] Build `widgets/quote_line_item_editor.dart` — add/remove materials + labor lines
- [ ] "Generate Follow-up" button → call tradie-followup endpoint → show draft dialog
- [ ] "Generate Invoice" button → call invoice/generate → PDF preview
- [ ] "Record Payment" inline on accepted quote detail

---

## P1 — Pipeline Integration

### FC-3: Email → Lead Extraction
- [ ] Add "Extract Lead" icon button on inbox email cards
- [ ] Build `widgets/lead_extraction_dialog.dart` — editable field preview
- [ ] Wire extraction dialog → save → navigate to construction tab

### FC-4: Inbox Approval Enhancements
- [ ] Tier filter chips row (URGENT / HIGH / MEDIUM / LOW / SPAM)
- [ ] Multi-select mode with batch approve/archive buttons
- [ ] Draft editor with "Revise with AI" option
- [ ] Undo snackbar after approve/archive (60s window)

---

## P2 — Voice Integration

### FC-5: Voice Command Wiring
- [ ] Pass screen_context + tab_index + selected_item_id to VoiceCommandService
- [ ] Integrate TTS playback after voice response (`audioplayers` package)
- [ ] Multi-turn follow-up UI in VoiceRecordingOverlay
- [ ] Parameter collection progress bar in VoiceConfirmationCard
- [ ] Voice-triggered navigation (response navigateTo → switch AppShell tab)

---

## P3 — Polish & Completeness

### FC-6: Dashboard Overview Cards
- [ ] Build `widgets/pipeline_revenue_card.dart` — revenue breakdown by status
- [ ] Aging report — highlight quotes pending >7 days
- [ ] Action feed — last 10 approvals/leads/payments

### FC-7: Site Visits & Job Files
- [ ] CRUD endpoints for `site_visits` in `routes/construction.py`
- [ ] CRUD endpoints for `job_files` with file upload
- [ ] Site visit tab in quote detail (date, notes, materials, actions)
- [ ] File attach button (camera + gallery + file picker)
- [ ] File gallery grid in quote detail

---

## Backlog (Not Prioritized)

- [ ] Persistent voice session across screen navigation
- [ ] Confirmation phrase matching ("say 'send it' to confirm") in Flutter
- [ ] Action history / undo log screen
- [ ] Business instructions context in voice responses
- [ ] Client-specific pipeline view
- [ ] Historical revenue trending chart
- [ ] Push notifications for new T1/T2 emails
- [ ] Offline mode with sync queue
- [ ] Test suite (pytest for backend, widget tests for Flutter)
- [ ] PostgreSQL migration for production
