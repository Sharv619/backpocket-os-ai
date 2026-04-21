# FULL AUDIT AND MIGRATION PLAN: BackPocket OS (2026-04-21)

## 1. Executive Audit: "The One-Man Army" Vision

Based on the PRD feedback and current codebase audit, we are transitioning from a general AI assistant to a **mission-critical Digital Twin** for trade businesses (e.g., Steve the Builder).

### 🚨 Critical Findings
1. **Naming Mismatch**: Existing twins (Accountant/Auditor) are too corporate. Need renaming to **Estimator** and **Site Manager**.
2. **"Amnesia" Risk**: While instructions are persisted in SQLite, real-time "learned" preferences from Steve need to be automatically promoted to permanent rules.
3. **Offline Gap**: Tradies lose 4G in metal sheds/rural sites. The Flutter app must queue voice recordings and process them once reception returns.
4. **Legal Liability**: Australian AI Safety Standards require "Human-in-the-loop". Every AI draft must be reviewable before sending/taking action.

---

## 2. Updated Architecture (Portable & Local)

- **Backend**: Python (FastAPI) + SQLite (`backpocket.db`). 
- **AI Stack**: Google Gemini (Cloud) for high-speed triage; Ollama (Local) for privacy & fallback.
- **Mobile**: Flutter (iOS/Android). Local persistence via `shared_preferences` (settings) and `sqflite` (offline queue).
- **Deployment**: Portable to a $300 Mini-PC, fulfilling the "local privacy" promise.

---

## 3. Implementation Chunks (Phase 2 Migration)

### CHUNK 1: Branding & Persona Overhaul
**Goal**: Move away from "Corporate AI" to "Site Buddy".
- **Flutter**: Update `agentic_rag_screen.dart` and `main.dart` to use:
    - **Estimator Twin** (Blue) - Measurements, Quotes, Leads.
    - **Site Manager Twin** (Green) - Documents, OCR, Marketing.
    - **Admin Twin** (Red) - Inbox Triage, Scheduling.
- **Backend**: Update `prompts/` and `services/twin_brain.py` to use these personas in system instructions.

### CHUNK 2: Offline Voice Resilience
**Goal**: Handle the "No Reception" problem.
- **Flutter**: Modify `voice_input_screen.dart`.
- **Logic**: If `api_service.sendVoiceCommand` fails due to network (Connectivity check):
    1. Save transcript + audio blob (if available) to local `sqflite` table `offline_commands`.
    2. Show notification: "In offline mode. Pip will process this as soon as you have reception."
    3. Add a background task (WorkManager) to retry when online.

### CHUNK 3: Permanent Memory (Fixing "Amnesia")
**Goal**: Persist Steve's "Teaching" moments.
- **Backend**: Modify `services/memory.py` or `services/twin_brain.py`.
- **Logic**: Create a `POST /api/instructions/promote` endpoint. When Steve corrects a draft or gives feedback in `TwinChat`, Pip should ask: *"Should I remember this rule for next time?"*. If Yes, save to the `instructions` table in `backpocket.db`.

### CHUNK 4: High-Priority Tradie Tools
**Goal**: Direct ROI for Steve.
1. **Receipt-OCR-Scanner**:
    - **UI**: Add "Scan Receipt" button in `DocumentsScreen`.
    - **Action**: Camera capture -> `api/documents/analyze-material` -> Map to Line Items.
2. **Voice-Invoice-Builder**:
    - **UI**: Integration in `ConstructionScreen` (Quotes tab).
    - **Action**: "Hey Pip, create an invoice for John Doe for 4 hours of plumbing and a new U-bend." -> AI generates Draft -> Steve Approves -> PDF Generated.

### CHUNK 5: Legal & Safety Guardrails
**Goal**: Australian Government AI Compliance.
- **UI**: Every AI-generated draft must have a **"Verify & Send"** button, never just "Send".
- **Disclaimer**: Add a subtle footer in `TwinChat`: *"AI-generated suggestions. Steve remains the final authority."*

---

## 4. Current Progress & Gap Analysis (Audit)

| Feature | API Status | Flutter UI Status | Priority |
|---|---|---|---|
| Twin Renaming | Backend Ready | **NEEDS UPDATE** | P0 |
| Persistence | Basic Table | **MISSING AUTO-LEARN** | P0 |
| Offline Queue | **MISSING** | **MISSING** | P1 |
| Receipt OCR | `analyze-material` ✅ | **UI NEEDED** | P1 |
| Voice Invoice | `invoice/generate` ✅ | **UI NEEDED** | P1 |
| Human-in-loop | `revise/save` ✅ | `inbox_screen` Partial | P0 |

---

## 5. Execution Steps (Next 24 Hours)


1. **Update `api_service.dart`**: Add missing methods for `promoteInstruction` and `generateInvoicePdf`.
2. **Refactor Screens**: Rename Twins in `agentic_rag_screen.dart`.
3. **Implement Offline Cache**: Add `sqflite` dependency and basic queueing logic.
4. **Draft Approval**: Complete the `CHUNK 2: Email Approval Modal` from the original plan.

---

*Full Audit Completed by Gemini CLI (2026-04-21)*
