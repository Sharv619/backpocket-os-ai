# Focus Chain — BackPocket MVP Workflow Implementation

> Priority-ordered implementation chain. Each link unlocks the next.
> Last updated: 2026-04-18

---

## P0 — Core Business Value

### FC-1: Construction Pipeline Stage Tracker
**Goal**: Visualize the 9-stage job lifecycle per lead
**Backend**:
- Add `workflow_stage` column to `leads` table (default: 1)
- `PATCH /api/construction/leads/{id}/stage` — advance/set stage
- Auto-advance rules: quote sent → stage 5, accepted → stage 7, payment received → stage 9

**Flutter**:
- New `widgets/workflow_stage_tracker.dart` — horizontal stepper with branch at stage 6
- Embed in lead detail view (construction_screen.dart)
- Embed summary on dashboard_screen.dart

**Done when**: User taps a lead → sees which stage it's at → can advance it.

---

### FC-2: Lead → Quote → Invoice Pipeline UI
**Goal**: Full pipeline flow inside Flutter construction tab
**Backend**: Endpoints already exist. No new backend work.

**Flutter**:
- "Create Quote" button on lead detail → pre-fills client_name, job_type, location from lead
- Quote line item editor (materials + labor breakdown) using `quote_line_items` table
- "Generate Follow-up" button → calls `POST /api/construction/quotes/{id}/tradie-followup` → show draft in dialog
- "Generate Invoice" button → calls `POST /api/invoice/generate` → PDF preview/download
- "Record Payment" button on accepted quote → record payment inline

**Done when**: User can go from lead → create quote → send → generate invoice → record payment — all from Flutter.

---

## P1 — Pipeline Integration

### FC-3: Email → Lead Extraction
**Goal**: One-tap lead extraction from inbox emails
**Backend**: `POST /api/construction/leads/extract` exists. No new backend.

**Flutter**:
- "Extract Lead" icon button on each inbox card (inbox_screen.dart)
- New `widgets/lead_extraction_dialog.dart` — shows AI-extracted fields (name, job_type, location, budget, urgency) with edit capability
- "Save Lead" → creates lead → shows snackbar → optional navigate to construction tab

**Done when**: User sees email about a job → taps extract → reviews fields → saves as lead.

---

### FC-4: Inbox Approval Enhancements
**Goal**: Filter, batch, and undo inbox actions
**Flutter**:
- Tier filter chips row at top of inbox (URGENT / HIGH / MEDIUM / LOW / SPAM)
- Multi-select mode with "Batch Approve" and "Batch Archive" buttons
- Draft editor with "Revise with AI" option (calls `/api/revise`)
- Undo snackbar after approve/archive (60s window, calls undo endpoint)

**Done when**: User can filter by tier, batch-approve 5 emails at once, undo a mistake.

---

## P2 — Voice Integration

### FC-5: Voice Command Wiring
**Goal**: Connect existing voice backend to Flutter screens
**Backend**: 50+ intents built. State machine built. Handlers built.

**Flutter**:
- Pass `screen_context`, `tab_index`, `selected_item_id` from AppShell to VoiceCommandService on every FAB tap
- Wire TTS playback: after voice response, call `POST /api/voice/tts` → play audio via `audioplayers` package
- Multi-turn follow-up UI: when `needsMoreInput=true`, show iterative question card in overlay
- Parameter collection progress bar (e.g., "Step 3 of 6: What's the budget?")
- Voice-triggered navigation: when response has `navigateTo`, switch AppShell tab

**Done when**: User says "create a lead for John in Penrith, kitchen reno" → voice walks through all fields → lead created.

---

## P3 — Polish & Completeness

### FC-6: Dashboard Overview Cards
**Goal**: At-a-glance business state on dashboard
**Flutter**:
- Pipeline revenue card — draft/sent/accepted $ breakdown with color bars
- Aging report — quotes pending >7 days highlighted amber, >14 days red
- Action feed — last 10 actions (approvals, new leads, payments) with timestamps

**Done when**: Dashboard shows revenue pipeline, stale quotes, and recent activity.

---

### FC-7: Site Visits & Job Files
**Goal**: Track onsite inspections and attach files to quotes
**Backend**:
- CRUD endpoints for `site_visits` (create, list by quote_id, update)
- CRUD endpoints for `job_files` (upload, list by quote_id, delete)
- File upload via `POST /api/construction/quotes/{id}/files` (save to `uploads/`)

**Flutter**:
- Site visit tab in quote detail (date picker, notes field, materials checklist, action items)
- File attach button (camera + gallery + file picker) → upload to backend
- File gallery grid in quote detail

**Done when**: User can log a site visit with notes, attach photos/plans to a quote.

---

## Dependency Graph

```
FC-1 (Stage Tracker) ──→ FC-2 (Pipeline UI) ──→ FC-3 (Email→Lead)
                                                       ↓
FC-4 (Inbox Enhance) ←─────────────────────────────────┘
         ↓
FC-5 (Voice Wiring) ──→ FC-6 (Dashboard) ──→ FC-7 (Site Visits)
```

## New Files Created

| File | Purpose |
|------|---------|
| `widgets/workflow_stage_tracker.dart` | Reusable 9-stage stepper widget |
| `widgets/lead_extraction_dialog.dart` | Email→lead preview/confirm dialog |
| `widgets/pipeline_revenue_card.dart` | Revenue breakdown dashboard card |
| `widgets/quote_line_item_editor.dart` | Materials/labor line item editor |

## Files Modified

| File | Changes |
|------|---------|
| `services/database.py` | `workflow_stage` column on leads |
| `routes/construction.py` | Stage advance endpoint, site visit + file CRUD |
| `screens/construction_screen.dart` | Stage tracker, invoice, follow-up, line items |
| `screens/inbox_screen.dart` | Tier filters, extract lead, batch mode |
| `screens/dashboard_screen.dart` | Pipeline card, aging report, action feed |
| `main.dart` | Voice context passing |
| `services/voice_command_service.dart` | TTS playback, screen context |
