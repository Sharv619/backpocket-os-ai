# Flutter Migration Plan: HTML Dashboard -> Flutter App

> **Purpose**: This document is the single source of truth for migrating every feature from `static/index.html` (5116 lines) into the Flutter app at `flutter_prototype/backpocket_mobile/`. Each chunk is self-contained and should be committed separately.
>
> **For smaller models**: Each chunk section contains exact file paths, API endpoints, and what to build. Follow each chunk literally. When done, `git add` the changed files and commit with the message shown.

---

## Current State

### Flutter App Structure
```
lib/
  main.dart                  - App shell, sidebar, bottom nav, 8 tabs (IndexedStack)
  theme.dart                 - AppColors, text styles
  screens/
    dashboard_screen.dart    - Home screen (health, workflow stages, greeting)
    inbox_screen.dart        - Email pending items with tier badges
    twin_chat_screen.dart    - Pip AI chat (basic)
    documents_screen.dart    - Document upload + list + analysis
    marketing_screen.dart    - GBP posts, social media
    instructions_screen.dart - Twin instructions CRUD
    construction_screen.dart - Leads, quotes, payments tabs
    settings_screen.dart     - Server URL, API key, owner name
    vision_chat_screen.dart  - Document vision AI chat
    voice_input_screen.dart  - Voice commands
    voice_help_screen.dart   - Voice help reference
  services/
    api_client.dart          - HTTP client with base URL + API key
    api_service.dart         - All API call methods
    tts_service.dart         - Text-to-speech
    voice_command_service.dart - Voice command processing
  widgets/
    voice_fab.dart           - Floating action button for voice
    voice_confirmation_card.dart - Voice response card
    voice_recording_overlay.dart - Recording UI overlay
```

### Navigation (main.dart)
- Bottom nav: Home(0), Inbox(1), Chat(2), Jobs(3), Settings(4)
- Sidebar drawer: Home, Inbox, Pip Chat, Documents, Marketing, Instructions, Construction, Settings
- Pages array index: 0=Dashboard, 1=Inbox, 2=TwinChat, 3=Documents, 4=Marketing, 5=Instructions, 6=Construction, 7=Settings

### Backend API Base URL
- Default: `http://127.0.0.1:8000`
- Configurable in Settings screen, stored in SharedPreferences as `server_url`
- API key header: `X-API-Key` (stored as `api_key`)

---

## Features in HTML NOT in Flutter (Gap Analysis)

| # | Feature | HTML Location | API Endpoint | Flutter Status |
|---|---------|--------------|--------------|----------------|
| 1 | Email approval modal (view draft, edit, approve/send) | `openModal()` L4165 | `GET /api/draft/{ref_id}`, `POST /api/approve`, `POST /api/revise` | MISSING |
| 2 | Email archive | `archiveItem()` L4265 | `POST /api/archive` | MISSING |
| 3 | SOPs (Standard Operating Procedures) | `loadSOPs()` L3334 | `GET /api/sops` | MISSING |
| 4 | Email triage rules viewer | `loadEmailRules()` L3346 | `GET /api/email-rules` | MISSING |
| 5 | Email rule change requests | `requestEmailRuleChange()` L3441 | `POST /api/instructions` | MISSING |
| 6 | Sender-specific rules CRUD | `loadSenderRules()` L3712 | `GET/POST/DELETE /api/sender-instructions` | MISSING |
| 7 | Agentic RAG analysis | `loadAgenticRAG()` L4647 | `GET /api/agentic-rag/context/{ref_id}` | MISSING |
| 8 | Agentic twins display | `loadAgenticTwins()` L4684 | N/A (static display) | MISSING |
| 9 | Blog post generation | `generateBlog()` L4752 | `GET /api/blog/generate?title=X&theme=Y` | MISSING |
| 10 | Startup story generation | `generateStartupStory()` L4786 | `POST /api/blog/startup-story` | MISSING |
| 11 | Blog library | `loadBlogLibrary()` L4710 | N/A (placeholder) | MISSING |
| 12 | Google Drive folder viewer | `loadDriveFolder()` L4715 | `POST /api/drive/sync-to-rag` | MISSING |
| 13 | Google Sheets / Client CRM | `loadClientMaster()` L3829 | `GET /api/client-master` | MISSING |
| 14 | Voice invoice (speech-to-text + PDF) | `createVoiceInvoice()` L4508 | `POST /api/invoice/generate` | PARTIAL (voice exists, invoice gen missing) |
| 15 | Chat slash commands (/pending, /approve, /revise, /coach, /status, /help) | `handleCommandInput()` L4049 | `POST /api/twin-chat` | MISSING |
| 16 | Chat conversation history (Pip + Open) | `loadConversations()` L2964 | `GET /api/conversations` | MISSING |
| 17 | Email workflow stats (pending/processed/rules) | `loadEmail()` L4932 | `GET /api/email-rules` | MISSING |
| 18 | Document workflow stats (total/pending/processed) | `loadDocs()` L4965 | `GET /api/documents` | PARTIAL |
| 19 | Marketing workflow stats (posts/engagement/followers) | `loadMarketing()` L4998 | `GET /api/marketing/activity` | PARTIAL |
| 20 | Task workflows | `loadTasks()` L5040 | `GET /api/workflow/stages` | PARTIAL |
| 21 | Document/Marketing/Client category rules | `loadCategoryInstructions()` L3993 | `GET /api/instructions` (filtered) | MISSING |
| 22 | Magnifier mode (accessibility zoom) | `toggleMagnifier()` L3034 | N/A (client-side) | MISSING |
| 23 | Greeting (time-of-day) | `setGreeting()` L3041 | N/A (client-side) | EXISTS (dashboard) |

---

## Migration Chunks

Each chunk is designed to be completable in a single session. Commit after each.

---

### CHUNK 1: API Service Methods (Foundation)
**Commit message**: `feat(flutter): add missing API service methods for full HTML parity`

**What**: Add all missing API call methods to `api_service.dart`. Every subsequent chunk depends on this.

**File**: `flutter_prototype/backpocket_mobile/lib/services/api_service.dart`

**Add these methods**:

```dart
// --- Email Approval Flow ---
// GET /api/draft/{ref_id} -> returns {draft: {draft_body, sender, subject, ...}}
Future<Map<String, dynamic>> getDraft(String refId)

// POST /api/approve with body {ref_id: "..."} -> returns {status: "success"}
Future<Map<String, dynamic>> approveEmail(String refId)

// POST /api/archive with body {ref_id: "..."} -> returns {status: "success"}
Future<Map<String, dynamic>> archiveEmail(String refId)

// POST /api/revise with body {ref_id: "...", new_draft: "...", feedback: "..."} -> returns {status: "success"}
Future<Map<String, dynamic>> reviseDraft(String refId, String newDraft, {String feedback = ''})

// --- SOPs ---
// GET /api/sops -> returns {sops: [{id, title, description, category, steps: "[...]"}, ...]}
Future<Map<String, dynamic>> getSops()

// --- Email Rules ---
// GET /api/email-rules -> returns {golden_senders: [...], processing_layers: [...], rules: [...]}
Future<Map<String, dynamic>> getEmailRules()

// --- Sender Instructions ---
// GET /api/sender-instructions -> returns {instructions: [{sender_email, instructions, category}, ...]}
Future<Map<String, dynamic>> getSenderInstructions()

// POST /api/sender-instructions with body {sender_email, instructions, category}
Future<Map<String, dynamic>> addSenderInstruction(String email, String instructions, String category)

// DELETE /api/sender-instructions/{sender_email}
Future<Map<String, dynamic>> deleteSenderInstruction(String senderEmail)

// --- Agentic RAG ---
// GET /api/agentic-rag/context/{ref_id} -> returns {email: {...}, agentic_analysis: {twin, system_prompt, learned_patterns}}
Future<Map<String, dynamic>> getAgenticRagContext(String refId)

// --- Blog ---
// GET /api/blog/generate?title=X&theme=Y -> returns {title, content, created_at}
Future<Map<String, dynamic>> generateBlogPost(String title, String theme)

// POST /api/blog/startup-story with body {company_name, theme} -> returns {title, content, company, style, created_at}
Future<Map<String, dynamic>> generateStartupStory(String companyName, {String theme = 'entrepreneurship'})

// --- Drive ---
// POST /api/drive/sync-to-rag with body {folder_id, twin_type} -> returns {ingested, total_files}
Future<Map<String, dynamic>> syncDriveToRag(String folderId, {String twinType = 'admin'})

// --- Client Master ---
// GET /api/client-master -> returns {status, count, clients: [{first_name, last_name, primary_email, client_status, mobile, background_info}, ...]}
Future<Map<String, dynamic>> getClientMaster()

// --- Conversations ---
// GET /api/conversations -> returns {conversations: [{id, title, source, updated_at}, ...]}
Future<Map<String, dynamic>> getConversations()

// GET /api/conversations/{id} -> returns {messages: [{role, content}, ...]}
Future<Map<String, dynamic>> getConversation(String conversationId)

// DELETE /api/conversations/{id}
Future<Map<String, dynamic>> deleteConversation(String conversationId)

// --- Invoice ---
// POST /api/invoice/generate with body {client_name, client_email, items: [{description, qty, rate, gst}], notes}
// Returns binary PDF blob
Future<List<int>> generateInvoicePdf(String clientName, String clientEmail, List<Map<String, dynamic>> items, {String notes = ''})
```

**How to implement**: Follow the existing pattern in `api_service.dart`. All methods use `http.get/post/delete` with `_headers()` and `_url(path)` helpers. Return decoded JSON maps. For the PDF endpoint, return `response.bodyBytes` instead of JSON.

---

### CHUNK 2: Email Approval Modal
**Commit message**: `feat(flutter): add email approval modal with draft editing`

**What**: When user taps an email in InboxScreen, show a bottom sheet / full-screen modal with:
- Subject line, sender, ref ID
- Editable draft text (TextField, multiline)
- 3 buttons: Archive, Save Draft, Approve & Send
- Confirmation dialog before sending

**Files to modify**:
- `lib/screens/inbox_screen.dart` — add `_openApprovalModal(item)` method
- Uses: `apiService.getDraft(refId)`, `apiService.reviseDraft(refId, newDraft)`, `apiService.approveEmail(refId)`, `apiService.archiveEmail(refId)`

**UI reference** (from HTML L4165-4258):
- Modal title: "Email Review"
- Shows From, Subject, Ref ID fields
- Large textarea for draft body
- Footer: Archive (grey), Save Draft (outlined), Approve & Send (primary green)
- On approve: confirm dialog "Send email to {sender}? '{first 100 chars}...'"

**Behavior**:
1. `onTap` of inbox item -> call `getDraft(item.ref_id)` 
2. Show `showModalBottomSheet` or `Navigator.push` to detail page
3. Pre-fill TextField with `draft.draft_body`
4. Archive -> call `archiveEmail`, pop, refresh list
5. Save Draft -> call `reviseDraft` with edited text, show SnackBar "Draft saved!"
6. Approve -> confirm dialog -> `reviseDraft` then `approveEmail` -> pop, refresh, SnackBar "Email sent!"

---

### CHUNK 3: SOPs Screen
**Commit message**: `feat(flutter): add SOPs screen with category filtering`

**What**: New screen showing Standard Operating Procedures with category filter chips.

**New file**: `lib/screens/sops_screen.dart`

**Modify**: `lib/main.dart` — add SOPs to sidebar nav items and _pages list

**API**: `GET /api/sops` returns `{sops: [{id, title, description, category, steps: "[json array]"}, ...]}`

**UI** (from HTML L2427-2443, L3877-3916):
- Filter chips at top: All, System, Chat, Email, Instructions, Debug
- Card list below, each card shows:
  - Category badge + title
  - Description text
  - Expandable steps list (tap to toggle)
  - Steps are JSON array stored as string, need `jsonDecode(sop['steps'])`

**Behavior**:
1. On load, fetch SOPs
2. Filter by category chip selection
3. Tap card to expand/collapse steps

---

### CHUNK 4: Email Rules & Sender Rules
**Commit message**: `feat(flutter): add email triage rules and sender rules to instructions screen`

**What**: Add two new tabs/sections to the existing InstructionsScreen:
1. **Email Triage Rules** — shows tier system (1-5), golden senders, processing layers
2. **Sender Rules** — CRUD for per-sender email handling instructions

**File**: `lib/screens/instructions_screen.dart`

**API endpoints**:
- `GET /api/email-rules` -> `{golden_senders: [...], processing_layers: [...], tier_descriptions: {...}}`
- `GET /api/sender-instructions` -> `{instructions: [{sender_email, instructions, category}, ...]}`
- `POST /api/sender-instructions` (create/update)
- `DELETE /api/sender-instructions/{sender_email}` (delete)

**Email Rules UI** (HTML L3346-3427):
- Tier cards 1-5 (color-coded):
  - T1 RED: "REPLY NEEDED" — Important client emails
  - T2 ORANGE: "REVIEW NEEDED" — Non-urgent acknowledgment
  - T3 BLUE: "FYI ONLY" — Info emails
  - T4 GREY: "ARCHIVE" — Portal updates
  - T5 DARK GREY: "LOW PRIORITY" — Newsletters/spam
- Golden senders list (always Tier 1)
- Processing layers numbered list

**Sender Rules UI** (HTML L3712-3827):
- Card per sender: email, category badge, instructions text
- Edit button -> inline edit with TextField
- Delete button -> confirm dialog -> delete
- Add button -> dialog with email, instructions, category fields
- "Discuss with Pip" button -> navigate to TwinChat with pre-filled message

---

### CHUNK 5: Category Rules (Document, Marketing, Client)
**Commit message**: `feat(flutter): add document, marketing, and client rules sections`

**What**: Add 3 more rule categories to InstructionsScreen. All use the same API endpoint with category filtering.

**File**: `lib/screens/instructions_screen.dart`

**API**: `GET /api/instructions` -> `{general_instructions: [{id, instruction_text, category, is_critical, is_active}, ...]}`
- Filter by category containing: "Document", "Marketing", "Email - Sender" (for client rules)

**UI** (HTML L3993-4025):
- Each shows filtered list of instruction cards
- Card shows: truncated instruction text, category badge, "CRITICAL" badge if is_critical
- Add button using existing instruction creation flow
- Empty state: "No {category} rules yet. Add instructions via Twin Instructions."

---

### CHUNK 6: Agentic RAG Screen
**Commit message**: `feat(flutter): add Agentic RAG analysis and twin agents display`

**What**: New screen with 2 sections:
1. **Email Analysis** — RAG context for the first pending email
2. **Pip Agents** — static display of 3 twin agent cards

**New file**: `lib/screens/agentic_rag_screen.dart`

**Modify**: `lib/main.dart` — add to sidebar and _pages

**API**:
- `GET /api/pending` -> get first item's `ref_id`
- `GET /api/agentic-rag/context/{ref_id}` -> `{email: {subject}, agentic_analysis: {twin, system_prompt, learned_patterns}}`

**Email Analysis UI** (HTML L4647-4682):
- Shows: email subject, selected twin name, system prompt used, learned patterns count
- Refresh button

**Twin Agents UI** (HTML L4684-4708):
- 3 cards in a row (or column on mobile):
  - Accountant Twin (blue, icon: chart) — "Handles invoicing, BAS, tax compliance"
  - Auditor Twin (green, icon: check) — "Reviews documents, verifies compliance"
  - Admin Twin (red, icon: settings) — "Email triage, scheduling, automation"
- Tap card -> navigate to TwinChat with agent-specific message

---

### CHUNK 7: Blog & Content Generation Screen
**Commit message**: `feat(flutter): add blog post and startup story generation`

**What**: New screen with 3 tabs:
1. Generate Blog Post
2. Startup Stories
3. Blog Library (placeholder)

**New file**: `lib/screens/blog_screen.dart`

**Modify**: `lib/main.dart` — add to sidebar and _pages

**API**:
- `GET /api/blog/generate?title=X&theme=Y` -> `{title, content, created_at}`
- `POST /api/blog/startup-story` with `{company_name, theme}` -> `{title, content, company, style, created_at}`

**Blog Generate UI** (HTML L2544-2567):
- Title TextField
- Theme dropdown: entrepreneurship, innovation, leadership, growth
- "Generate Post" button (shows loading state)
- Output card below with title, date, content

**Startup Stories UI** (HTML L2569-2583):
- Company name TextField
- "Generate Startup Story" button
- Output card with title, date, content, company name, style tag

**Blog Library UI** (HTML L2585-2594):
- Placeholder: "Blog library coming soon..."

---

### CHUNK 8: Google Drive Integration Screen
**Commit message**: `feat(flutter): add Google Drive folder sync to RAG`

**What**: New screen for syncing Drive folders to RAG system.

**New file**: `lib/screens/drive_screen.dart`

**Modify**: `lib/main.dart` — add to sidebar and _pages

**API**: `POST /api/drive/sync-to-rag` with `{folder_id, twin_type}` -> `{ingested, total_files}`

**UI** (HTML L4715-4749):
- Folder icon + header text
- TextField for Google Drive Folder ID
- "Sync Folder" button
- Result display: "Synced X/Y files to RAG"
- Info text: "Connect a Google Drive folder to sync files to the RAG system."

---

### CHUNK 9: Client CRM (Google Sheets) Screen
**Commit message**: `feat(flutter): add Client CRM database view from Google Sheets`

**What**: New screen showing client data from Google Sheets.

**New file**: `lib/screens/client_crm_screen.dart`

**Modify**: `lib/main.dart` — add to sidebar and _pages

**API**: `GET /api/client-master` -> `{status, count, clients: [{first_name, last_name, primary_email, client_status, mobile, background_info}, ...]}`

**UI** (HTML L3829-3875):
- Header: "Client CRM Database" with client count
- DataTable or ListView with columns:
  - Name (first + last)
  - Email
  - Status
  - Mobile
  - Background
- Empty state: "No clients in BPS_Client_Master yet."
- Error state: show error message

---

### CHUNK 10: Chat Enhancements (Slash Commands + History)
**Commit message**: `feat(flutter): add slash commands and conversation history to Pip chat`

**What**: Enhance TwinChatScreen with:
1. Slash command autocomplete
2. Conversation history sidebar/drawer

**File**: `lib/screens/twin_chat_screen.dart`

**Slash Commands** (HTML L4046-4108):
- When user types `/` in TextField, show dropdown with:
  - `/pending` — Show pending approvals
  - `/approve` — Approve and send email (needs ref)
  - `/revise` — AI revise a draft (needs ref + feedback)
  - `/coach` — Analyze draft tone & clarity
  - `/status` — System health check
  - `/help` — List all commands
- Tap command -> insert into TextField
- Some auto-send (/pending, /status, /help)
- Implementation: use `Overlay` or `CompositedTransformFollower` widget

**Conversation History** (HTML L2964-3029):
- API: `GET /api/conversations` -> list of {id, title, source, updated_at}
- Split into "Pip Chat" (source=twin) and "Open Chat" (source=opencode)
- Show in sidebar drawer under chat section
- Tap conversation -> `GET /api/conversations/{id}` -> load messages
- Show relative time: "2m ago", "3h ago", "Apr 15"

---

### CHUNK 11: Voice Invoice PDF Generation
**Commit message**: `feat(flutter): add voice-to-invoice PDF generation`

**What**: Add invoice generation to the voice input flow.

**File**: `lib/screens/voice_input_screen.dart`

**API**: `POST /api/invoice/generate` with `{client_name, client_email, items: [{description, qty, rate, gst}], notes}`
- Returns: binary PDF bytes

**UI** (HTML L4405-4579):
- After voice input captured, show "Create Invoice" option
- Client name + email fields
- Parse voice text into line items (port `parseVoiceToItems` logic):
  - Match "X hours labour at $Y" -> {description: "Labour", qty: X, rate: Y, gst: true}
  - Match "materials $X" -> {description: "Materials", qty: 1, rate: X, gst: true}
  - Fallback: single line item with full text
- "Create Invoice PDF" button
- Download/share PDF using `share_plus` or `path_provider` + `open_file`

---

### CHUNK 12: Update Navigation + Cleanup
**Commit message**: `feat(flutter): update navigation for all new screens, remove HTML dashboard`

**What**: Wire up all new screens in navigation and remove HTML.

**Files to modify**:
- `lib/main.dart`:
  - Add imports for all new screens
  - Update `_buildPages()` list to include: SOPs, AgenticRAG, Blog, Drive, ClientCRM
  - Update sidebar nav items list with new entries
  - Keep bottom nav at 5 items (Home, Inbox, Chat, Jobs, Settings)
  - New screens accessible via sidebar only
- **DELETE**: `static/index.html` and all static/*.backup files
- **KEEP**: `static/assets/`, `static/icons/`, `static/manifest.json` (if used by mobile)

**Sidebar order** (matching HTML):
1. Home (tab 0)
2. Inbox (tab 1)
3. Pip Chat (tab 2)
4. Documents (tab 3)
5. SOPs (tab NEW)
6. Instructions (tab 5)
7. Email Rules (part of Instructions, or separate)
8. Marketing (tab 4)
9. Agentic RAG (tab NEW)
10. Blog (tab NEW)
11. Drive (tab NEW)
12. Client CRM (tab NEW)
13. Construction (tab 6)
14. Settings (tab 7)

**Bottom nav stays**: Home, Inbox, Chat, Jobs, Settings (most used)

---

## API Quick Reference

All endpoints relative to `{serverUrl}` (default `http://127.0.0.1:8000`).

| Endpoint | Method | Body | Returns |
|----------|--------|------|---------|
| `/api/pending` | GET | - | `{items: [{ref_id, subject, sender, tier, created_at}]}` |
| `/api/draft/{ref_id}` | GET | - | `{draft: {draft_body, sender, subject}}` |
| `/api/approve` | POST | `{ref_id}` | `{status: "success"}` |
| `/api/archive` | POST | `{ref_id}` | `{status: "success"}` |
| `/api/revise` | POST | `{ref_id, new_draft, feedback}` | `{status: "success"}` |
| `/api/sops` | GET | - | `{sops: [{id, title, description, category, steps}]}` |
| `/api/email-rules` | GET | - | `{golden_senders, processing_layers, rules}` |
| `/api/sender-instructions` | GET | - | `{instructions: [{sender_email, instructions, category}]}` |
| `/api/sender-instructions` | POST | `{sender_email, instructions, category}` | `{status}` |
| `/api/sender-instructions/{email}` | DELETE | - | `{status}` |
| `/api/instructions` | GET | - | `{general_instructions: [{id, instruction_text, category, is_critical}]}` |
| `/api/instructions` | POST | `{instruction_text, category, is_active, is_critical}` | `{status}` |
| `/api/instructions/{id}` | PUT | `{instruction_text, category, is_active, is_critical}` | `{status}` |
| `/api/instructions/{id}` | DELETE | - | `{status}` |
| `/api/agentic-rag/context/{ref_id}` | GET | - | `{email, agentic_analysis: {twin, system_prompt, learned_patterns}}` |
| `/api/blog/generate` | GET | query: `title`, `theme` | `{title, content, created_at}` |
| `/api/blog/startup-story` | POST | `{company_name, theme}` | `{title, content, company, style, created_at}` |
| `/api/drive/sync-to-rag` | POST | `{folder_id, twin_type}` | `{ingested, total_files}` |
| `/api/client-master` | GET | - | `{status, count, clients: [...]}` |
| `/api/conversations` | GET | - | `{conversations: [{id, title, source, updated_at}]}` |
| `/api/conversations/{id}` | GET | - | `{messages: [{role, content}]}` |
| `/api/conversations/{id}` | DELETE | - | `{status}` |
| `/api/twin-chat` | POST | `{message, chat_history}` | `{response}` |
| `/api/invoice/generate` | POST | `{client_name, client_email, items, notes}` | Binary PDF |
| `/api/construction/leads` | GET/POST | - / lead data | leads list / created lead |
| `/api/construction/quotes` | GET/POST | - / quote data | quotes list / created quote |
| `/api/construction/pipeline` | GET | - | `{data: {total_quotes, pending_quotes, accepted_quotes, revenue_pipeline}}` |
| `/api/construction/payments` | GET/POST | - / payment data | payments list / recorded payment |
| `/api/construction/leads/extract` | POST | `{from, subject, body}` | `{lead_id, ...extracted data}` |
| `/api/construction/quotes/{id}/tradie-followup` | POST | - | `{message}` |

---

## Theme Reference

Use the existing theme from `lib/theme.dart`:

```dart
// Key colors from AppColors class:
AppColors.brown      // Primary dark
AppColors.amber      // Primary accent  
AppColors.orange     // Secondary accent
AppColors.surface    // Card/surface background
AppColors.red        // Error/Tier 1
AppColors.green      // Success
```

Match the dark-themed look of the existing Flutter app. All new screens should use the same `Scaffold` + `AppBar` pattern with `AppColors.surface` background.

---

## Execution Order

**Do chunks in order 1-12.** Chunk 1 is required by all others. Chunks 2-11 are independent of each other but all need Chunk 1. Chunk 12 is last (wires everything together and deletes HTML).

**Commit after each chunk.** Push after every 2-3 chunks.

```
Chunk 1  -> git commit -> foundation (API methods)
Chunk 2  -> git commit -> email approval
Chunk 3  -> git commit -> SOPs
Chunk 4  -> git commit -> email rules + sender rules  
Chunk 5  -> git commit -> category rules
Chunk 6  -> git commit -> agentic RAG
Chunk 7  -> git commit -> blog generation
Chunk 8  -> git commit -> drive integration
Chunk 9  -> git commit -> client CRM
Chunk 10 -> git commit -> chat enhancements
Chunk 11 -> git commit -> voice invoice
Chunk 12 -> git commit -> nav update + HTML cleanup
```

---

## Notes for Smaller Models

1. **Always read the file first** before editing. Use `Read` tool on the target file.
2. **Follow existing patterns** — look at how existing screens are structured (constructor takes `serverUrl` + `apiKey`, uses `http` package, returns `Scaffold`).
3. **Don't modify theme.dart** — use existing `AppColors` and text styles.
4. **Test each chunk** — after each chunk, the app should still compile. Run `flutter analyze` in `flutter_prototype/backpocket_mobile/`.
5. **API calls pattern** — all use this format:
   ```dart
   final response = await http.get(
     Uri.parse('$serverUrl/api/endpoint'),
     headers: {'Content-Type': 'application/json', if (apiKey.isNotEmpty) 'X-API-Key': apiKey},
   );
   final data = jsonDecode(response.body);
   ```
6. **New screens need**: import in main.dart, added to `_buildPages()`, added to sidebar nav items list.
7. **Error handling**: wrap API calls in try/catch, show SnackBar on error. Follow existing screen patterns.
