# ⛓️ BackPocket OS: The Focus Chain

**Goal:** Transform the "Demo MVP" into a 100% functional, production-ready Digital Twin.
**Current Phase:** Phase 1 - The Core Engine
**Current Focus:** [ ] Step 1.3: The "Dual-Write" Postgres Migration

---

## 🏗️ PHASE 1: THE CORE ENGINE (The "Must-Haves")
*Objective: Get the plumbing working so we can handle money and users.*

- [x] **1.1: Stripe Finance Backend**
    - File: `services/stripe.py`
    - Task: Implement real `create_checkout_session`, `handle_webhook`, and `get_subscription_status`.
    - Status: ✅ COMPLETE (Monthly $25/mo and Lifetime $199 handled)

- [x] **1.2: RAG Context Injection**
    - File: `services/pgvector_rag.py`
    - Task: Actually inject retrieved ChromaDB memories into Gemini/Ollama prompts.
    - Status: ✅ COMPLETE (Wired to OpenRouter with Postgres context)

- [x] **1.3: The "Dual-Write" Postgres Migration**
    - File: `services/database.py` & `scripts/sqlite_to_pg_migration.py`
    - Task: Activate Postgres as the primary DB, keeping SQLite as a local fallback.
    - Status: ✅ COMPLETE (Migration run, Dual-write router active)

- [x] **1.4: Real Auth & RLS**
    - File: `services/auth.py`
    - Task: Replace "Dev Bypass" with Supabase JWT validation and Postgres Row Level Security.
    - Status: ✅ COMPLETE (JWT wired + Postgres RLS using contextvars)

---

## 🎤 PHASE 2: MOBILE & VOICE (The "Site Manager")
*Objective: Make the app actually work on a construction site.*

**Current Focus:** [ ] Step 3.1: OCR Pipeline Implementation

---

## 🎤 PHASE 2: MOBILE & VOICE (The "Site Manager")
*Objective: Make the app actually work on a construction site.*

- [x] **2.1: Flutter Real-Mic Integration**
    - File: `flutter_prototype/backpocket_mobile/lib/screens/voice_input_screen.dart`
    - Task: Replace `AudioRecorder` stub with `flutter_sound`.
    - Status: ✅ COMPLETE (Replaced `record` package with `flutter_sound` + permissions check)

- [x] **2.2: Voice-to-Action Pipeline**
    - File: `routes/voice.py` & `services/voice_to_actions.py`
    - Task: Map transcripts to "Materials needed" or "Subcontractors to call" entries in DB.
    - Status: ✅ COMPLETE (Pipeline built, site visits parsing + DB inserts wired)

- [x] **2.3: Offline Command Queue**
    - File: Flutter `sqflite` implementation.
    - Task: Queue voice blobs locally and sync when 4G returns.
    - Status: ✅ COMPLETE (Added `syncOfflineCommands` and `connectivity_plus` listener to app shell)
**Current Focus:** [ ] Step 4.1: MCP Restructure

---

## 📄 PHASE 3: DOCUMENT INTELLIGENCE (The "Eyes")
*Objective: Automate the paperwork trail.*

- [x] **3.1: OCR Pipeline Implementation**
    - File: `services/documents/ocr.py`
    - Task: Integrate native Python PyPDF2 extraction (bypassing broken docker dependencies) with Vision API stubs.
    - Status: ✅ COMPLETE (Native extraction built and wired to upload endpoint)

- [x] **3.2: Receipt-to-Payment Extractor**
    - File: `services/documents/extractor.py`
    - Task: AI-extract line items from Bunnings/Supplier receipts into `payments` table.
    - Status: ✅ COMPLETE (Built local Ollama extraction and integrated into upload route)

---

## 🛠️ PHASE 4: VIBECODING & ORCHESTRATION (The "Speed")
*Objective: Make the system help us build itself.*

- [ ] **4.1: MCP Restructure**
    - File: `mcp_servers/*.mjs`
    - Task: Split broken Node monolith into 4 thin servers (Leads, Quotes, Pipeline, Knowledge).
    - Status: 🔴 NOT STARTED

- [ ] **4.2: Shared Knowledge Hook**
    - File: `scripts/git-hooks/post-merge`
    - Task: Auto-capture every git commit into the Twin's permanent memory.
    - Status: 🔴 NOT STARTED

---

## 📢 PHASE 5: THE POLISH (Marketing & Coaching)
*Objective: Add the "WOW" features.*

- [ ] **5.1: Communication Coach Checkers**
    - File: `services/coach/*.py`
    - Task: Implement Empathy, Authority, and Clarity scanners for AI drafts.
    - Status: 🔴 NOT STARTED

- [ ] **5.2: Social Media Scheduler**
    - File: `services/marketing/scheduler.py`
    - Task: Build the queue for Facebook/Instagram delayed posts.
    - Status: 🔴 NOT STARTED

---

## 🚦 EXECUTION LOG
*Track our wins here.*

- [2026-04-21] Initialized Focus Chain.
