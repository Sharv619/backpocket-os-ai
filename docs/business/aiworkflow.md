# BackPocket OS -- AI Voice Workflow Specification

**Version:** 1.0
**Date:** 2026-04-17
**Status:** Spec Complete -- Ready for Implementation

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Voice Command Router](#2-voice-command-router)
3. [Intent Classification](#3-intent-classification)
4. [Per-Screen Workflows](#4-per-screen-workflows)
5. [Cross-Screen Workflows](#5-cross-screen-workflows)
6. [Multi-Turn Conversation State Machine](#6-multi-turn-conversation-state-machine)
7. [Confirmation & Safety](#7-confirmation--safety)
8. [Response Format](#8-response-format)
9. [New Backend Endpoints](#9-new-backend-endpoints)
10. [New Files Required](#10-new-files-required)
11. [Error Handling](#11-error-handling)
12. [Implementation Phases](#12-implementation-phases)

---

## 1. Architecture Overview

Voice commands flow through three new layers stacked on top of the existing API:

```
                        +----------------------------+
                        |   Flutter Voice FAB (Mic)   |  <- Every screen
                        +----------------------------+
                                    |
                                    v
                        +----------------------------+
                        |  Layer 1: Voice Capture     |  <- Real mic recording
                        |  (flutter_sound / record)   |     replaces stubbed AudioRecorder
                        +----------------------------+
                                    |  audio file
                                    v
                        +----------------------------+
                        |  POST /api/voice/transcribe |  <- Existing endpoint
                        |  (Ollama Whisper / Gemini)  |     already built in routes/voice.py
                        +----------------------------+
                                    |  transcript text
                                    v
                        +----------------------------+
                        |  Layer 2: Voice Command     |  <- NEW: Central router
                        |  Router                     |
                        |  POST /api/voice/command    |
                        |  - Intent classification    |
                        |  - Entity extraction        |
                        |  - Fuzzy matching           |
                        |  - Action dispatch          |
                        +----------------------------+
                                    |  calls existing endpoints internally
                                    v
                  +----------------------------------+
                  |  Existing API Layer               |
                  |  /api/mobile/*                    |
                  |  /api/construction/*              |
                  |  /api/documents/*                 |
                  |  /api/marketing/*                 |
                  |  /api/instructions                |
                  +----------------------------------+
                                    |
                                    v
                        +----------------------------+
                        |  Layer 3: State Machine     |  <- NEW: Multi-turn sessions
                        |  (voice_session.py)         |
                        |  IDLE -> COLLECTING ->      |
                        |  CONFIRMING -> EXECUTING    |
                        +----------------------------+
                                    |  structured result
                                    v
                        +----------------------------+
                        |  Response Generator         |  <- NEW: Natural language + TTS
                        |  (voice_response.py)        |
                        |  POST /api/voice/tts        |     existing ElevenLabs endpoint
                        +----------------------------+
                                    |  speech + ui_action
                                    v
                        +----------------------------+
                        |  Flutter UI Update          |  <- Navigate, highlight, refresh
                        +----------------------------+
```

**Key principle:** Voice is a new *input modality*, not a new feature set. Every voice command ultimately calls the same services and endpoints that the UI buttons already use. The Voice Command Router is an orchestration layer, not a parallel system.

---

## 2. Voice Command Router

### Endpoint: `POST /api/voice/command`

**Request:**
```json
{
  "transcript": "chuck a quote together for the bloke in Penrith",
  "screen_context": "construction",
  "session_id": "uuid-session-123",
  "metadata": {
    "selected_item_id": null,
    "tab_index": 1
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transcript` | string | Yes | Raw transcribed text from Whisper |
| `screen_context` | string | Yes | Current screen: `dashboard`, `inbox`, `chat`, `documents`, `marketing`, `instructions`, `construction`, `settings` |
| `session_id` | string | Yes | UUID for multi-turn conversation tracking |
| `metadata.selected_item_id` | int/null | No | If user has an item selected/focused on screen |
| `metadata.tab_index` | int/null | No | For tabbed screens (construction: 0=leads, 1=quotes, 2=payments) |

**Response:**
```json
{
  "intent": "construction.quote.create",
  "confidence": 0.92,
  "action": "confirm",
  "result": {
    "lead_id": 5,
    "lead_name": "John Smith",
    "job_type": "Bathroom Renovation",
    "location": "Penrith"
  },
  "speech_response": "Found the lead -- John Smith, bathroom reno in Penrith. What are the materials going to cost?",
  "ui_action": {
    "navigate_to": "construction",
    "tab_index": 1,
    "highlight_item": null,
    "show_modal": null,
    "refresh_data": false
  },
  "needs_confirmation": false,
  "follow_up_prompt": "Materials cost?",
  "session_state": {
    "state": "COLLECTING",
    "intent": "construction.quote.create",
    "collected_params": {"lead_id": 5},
    "missing_params": ["materials_cost", "labor_cost", "markup_percent"]
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `intent` | string | Classified intent (dot-notation) |
| `confidence` | float | 0.0--1.0 classification confidence |
| `action` | string | `execute` / `confirm` / `clarify` / `navigate` / `display` |
| `result` | object | Action result data (varies by intent) |
| `speech_response` | string | Text for TTS playback |
| `ui_action` | object | What Flutter should do (navigate, highlight, refresh) |
| `needs_confirmation` | bool | Whether to wait for yes/no before executing |
| `follow_up_prompt` | string | Next question for multi-turn (null if complete) |
| `session_state` | object | Updated session state for client to send back next turn |

---

## 3. Intent Classification

### Approach

Use Gemini 2.5-flash (already integrated in `services/gemini.py`) with a structured system prompt. No separate NLP model needed -- the LLM handles intent classification, entity extraction, and slang normalization in one call.

### Classification Prompt Template

```
You are the voice command classifier for BackPocket OS, a tradie business app.
The user is Steve, an Australian contractor. He speaks casually.

Current screen: {screen_context}
Active session: {session_state}
Available data context: {available_entities}

Classify the following voice command into an intent and extract parameters.

Command: "{transcript}"

Return JSON:
{
  "intent": "<screen>.<entity>.<action>",
  "entities": { extracted parameters },
  "confidence": 0.0-1.0,
  "ambiguity_reason": "reason if confidence < 0.7, else null"
}

INTENT TAXONOMY:
{full_intent_list}

TRADIE SLANG GUIDE:
- "chuck a quote together" = create_quote
- "give it the tick" / "she'll be right" = approve
- "knock it back" = reject
- "what's the damage" = get_total / pipeline
- "bang out an invoice" = generate_invoice
- "fire off that email" = approve_and_send
- "suss out" = analyze / review
- "that bloke in [suburb]" = fuzzy_match lead by location
- "arvo" = afternoon
```

### Full Intent Taxonomy

```
INTENT_TAXONOMY = {
    # ── Dashboard ────────────────────────────────────────────────
    "dashboard.summary":           {params: [],                           confirm: false},
    "dashboard.pending_count":     {params: [],                           confirm: false},
    "dashboard.pipeline_summary":  {params: [],                           confirm: false},
    "dashboard.navigate":          {params: ["target_screen"],            confirm: false},
    "dashboard.growth_stats":      {params: [],                           confirm: false},

    # ── Inbox ────────────────────────────────────────────────────
    "inbox.list":                  {params: ["filter_tier?"],             confirm: false},
    "inbox.filter_tier":           {params: ["tier"],                     confirm: false},
    "inbox.approve":               {params: ["ref_id|sender|subject"],   confirm: true},
    "inbox.approve_batch":         {params: ["tier"],                     confirm: true,  danger: "high"},
    "inbox.show_draft":            {params: ["ref_id|sender"],           confirm: false},
    "inbox.revise_draft":          {params: ["ref_id", "instructions"],  confirm: false},
    "inbox.read_email":            {params: ["sender_name"],             confirm: false},
    "inbox.count_by_tier":         {params: ["tier?"],                   confirm: false},

    # ── Chat ─────────────────────────────────────────────────────
    "chat.ask":                    {params: ["message"],                  confirm: false},
    "chat.clear":                  {params: [],                           confirm: false},

    # ── Documents ────────────────────────────────────────────────
    "documents.list":              {params: [],                           confirm: false},
    "documents.upload":            {params: ["source?"],                  confirm: false},
    "documents.analyze":           {params: ["doc_id?"],                  confirm: false},
    "documents.search":            {params: ["query"],                    confirm: false},

    # ── Marketing ────────────────────────────────────────────────
    "marketing.create_post":       {params: ["job_description", "suburb"], confirm: true},
    "marketing.insights":          {params: [],                           confirm: false},
    "marketing.activity":          {params: [],                           confirm: false},

    # ── Instructions ─────────────────────────────────────────────
    "instructions.list":           {params: [],                           confirm: false},
    "instructions.add":            {params: ["text", "category?"],       confirm: true},
    "instructions.delete":         {params: ["id|keyword"],              confirm: true},

    # ── Construction: Leads ──────────────────────────────────────
    "construction.lead.create":    {params: ["client_name", "job_type", "location", "budget?", "urgency?", "email?"], confirm: true},
    "construction.lead.list":      {params: ["status?"],                 confirm: false},
    "construction.lead.detail":    {params: ["lead_id|fuzzy"],           confirm: false},
    "construction.lead.update":    {params: ["lead_id", "status"],       confirm: true},
    "construction.lead.extract":   {params: ["email_ref_id"],            confirm: true},

    # ── Construction: Quotes ─────────────────────────────────────
    "construction.quote.create":   {params: ["lead_id", "materials_cost", "labor_cost", "markup_percent?"], confirm: true},
    "construction.quote.list":     {params: ["status?"],                 confirm: false},
    "construction.quote.detail":   {params: ["quote_id|fuzzy"],          confirm: false},
    "construction.quote.update":   {params: ["quote_id", "status"],      confirm: true},
    "construction.quote.followup": {params: ["quote_id"],                confirm: true},
    "construction.quote.invoice":  {params: ["quote_id"],                confirm: true},

    # ── Construction: Payments ───────────────────────────────────
    "construction.payment.record": {params: ["quote_id", "amount"],      confirm: true},
    "construction.payment.list":   {params: ["quote_id?"],               confirm: false},
    "construction.payment.pipeline":{params: [],                          confirm: false},

    # ── Cross-Screen ─────────────────────────────────────────────
    "cross.email_to_lead":         {params: ["ref_id|sender"],           confirm: true},
    "cross.lead_to_quote":         {params: ["lead_params+quote_params"],confirm: true},
    "cross.quote_to_invoice":      {params: ["quote_id|fuzzy"],          confirm: true},
    "cross.full_report":           {params: [],                           confirm: false},

    # ── Navigation ───────────────────────────────────────────────
    "navigate.screen":             {params: ["target"],                   confirm: false},

    # ── Meta ─────────────────────────────────────────────────────
    "meta.help":                   {params: [],                           confirm: false},
    "meta.cancel":                 {params: [],                           confirm: false},
    "meta.undo":                   {params: ["action_id?"],              confirm: true},
}
```

### Entity Resolution

When the user says "the Penrith one" or "that bloke from the email," the system must resolve fuzzy references against live data.

**Resolution chain:**
1. Check session state for recently created/viewed entity (context carry-forward)
2. Fuzzy match by name/location against current screen's data (leads, quotes, pending emails)
3. If multiple matches: ask user to pick ("Found 3 leads in Penrith -- John, Dave, or Sarah?")
4. If zero matches: report and offer to create ("No leads in Penrith. Want to create one?")

---

## 4. Per-Screen Workflows

### 4A. Dashboard

| Intent | Example Utterances | What Happens |
|--------|-------------------|--------------|
| `dashboard.summary` | "What's going on today?", "Give me the rundown", "Morning update" | Calls `/api/status` + `/api/construction/pipeline` + `/api/marketing/insights` in parallel. Gemini generates natural summary. TTS playback. |
| `dashboard.pending_count` | "How many emails need attention?" | Returns count from `/api/mobile/pending`. TTS: "You've got 27 emails waiting, 4 are urgent." |
| `dashboard.pipeline_summary` | "What's my pipeline?", "How are the jobs going?" | Returns from `/api/construction/pipeline`. TTS: "Pipeline's at $41,185. 2 pending quotes, 2 accepted." |
| `dashboard.navigate` | "Take me to inbox", "Open construction", "Go to documents" | Navigate to target screen. No TTS. |
| `dashboard.growth_stats` | "How's my SEO?", "Marketing numbers?" | Returns from `/api/marketing/insights`. TTS summary. |

**Example flow -- `dashboard.summary`:**
```
Steve: "What's going on today?"
Pip:   "Morning Steve. You've got 27 emails waiting -- 4 urgent.
        Pipeline's sitting at $41,185 across 8 quotes, 2 accepted.
        Local search is up 22% this week. Want me to start with the inbox?"
Steve: "Yeah go to inbox"
Pip:   [navigates to Inbox screen]
```

---

### 4B. Inbox

| Intent | Example Utterances | What Happens |
|--------|-------------------|--------------|
| `inbox.list` | "What emails do I have?", "Show me the inbox" | Refreshes inbox data. TTS count summary. |
| `inbox.filter_tier` | "Show me the urgent ones", "Just tier 1" | Filters display client-side. TTS: "Showing 4 urgent emails." |
| `inbox.approve` | "Approve that one", "Fire off the email to Sarah", "Give it the tick" | Fuzzy-match by sender/subject. Confirmation required. Then `POST /api/mobile/approve`. |
| `inbox.approve_batch` | "Approve all tier 1 emails", "Send all the urgent ones" | Strong confirmation. Loops `POST /api/mobile/approve` for each. |
| `inbox.show_draft` | "Show me the draft to Sarah", "What did Pip write for the kitchen quote?" | Fuzzy-match, navigate to detail screen. TTS reads draft. |
| `inbox.revise_draft` | "Make it more casual", "Rewrite that, too formal" | `POST /api/revise` with instructions. Shows revised draft. |
| `inbox.read_email` | "Read me the email from John" | Fuzzy-match by sender. TTS reads email preview + draft. |
| `inbox.count_by_tier` | "How many urgent emails?" | Count from cached data. TTS: "4 urgent, 8 high priority." |

**Example flow -- `inbox.approve` (with confirmation):**
```
Steve: "Approve the email to Sarah"
Pip:   "I'll send the draft to sarah@example.com about the kitchen renovation.
        Say 'send it' to confirm."
Steve: "Send it"
Pip:   "Done, email's sent to Sarah."
        [removes item from inbox list, refreshes]
```

**Example flow -- `inbox.approve_batch` (strong confirmation):**
```
Steve: "Approve all tier 1 emails"
Pip:   "That's 4 emails to tier 1 recipients:
        - Sarah Mitchell (kitchen reno)
        - Dave Wilson (bathroom quote)
        - Priya S (electrical)
        - James T (roofing)
        Say 'send them all' to confirm."
Steve: "Send them all"
Pip:   "All 4 sent. Inbox updated."
```

---

### 4C. Pip Chat (Fallback Brain)

Pip Chat is the **catch-all** screen. Any voice command that the router cannot classify with confidence > 0.7 gets routed here. The existing `/api/mobile/chat` endpoint handles free-form queries via the Twin system (Gemini + RAG + twin_brain context).

| Intent | Example Utterances | What Happens |
|--------|-------------------|--------------|
| `chat.ask` | Any unstructured question | `POST /api/mobile/chat`. TTS + display response. |
| `chat.clear` | "Start fresh", "New chat" | Clears local message history. |

**Fallback example:**
```
Steve: "What should I focus on today?"
        [Router confidence: 0.45 -- no specific intent match]
        [Routes to Pip Chat]
Pip:   "Based on your inbox, I'd tackle the 4 urgent emails first.
        You've also got the Penrith quote sitting at draft --
        might want to send that before the client goes elsewhere.
        Pipeline's healthy at $41k."
```

**Action escalation from chat:**
```
Steve: "Actually yeah, send that Penrith quote"
Pip:   [Re-classifies as construction.quote.update with status=sent]
        "Marking the Penrith bathroom quote as sent. Confirm?"
Steve: "Yeah"
Pip:   "Done. Quote sent to John Smith."
```

---

### 4D. Documents

| Intent | Example Utterances | What Happens |
|--------|-------------------|--------------|
| `documents.list` | "Show me my documents", "What docs do I have?" | `GET /api/documents`. TTS: "You've got 18 documents. 15 analyzed, 3 pending." |
| `documents.upload` | "Scan a document", "Take a photo of this receipt" | Triggers camera/gallery picker on device. |
| `documents.analyze` | "Analyze that last document", "What does this receipt say?" | `POST /api/documents/analyze/{id}`. TTS reads analysis summary. |
| `documents.search` | "Find the invoice from March" | Searches documents by name/date. Shows filtered list. |

**Example flow -- `documents.upload` + `documents.analyze`:**
```
Steve: "Scan a receipt"
Pip:   [Opens camera]
Steve: [Takes photo]
Pip:   "Got it. Uploading... Analyzing with AI..."
        [POST /api/documents/upload, then POST /api/documents/analyze/{id}]
Pip:   "Receipt from Bunnings. $847.50 for bathroom tiles,
        grout, and silicone. Date: April 15. Want me to log this
        against a quote?"
Steve: "Yeah, the Penrith bathroom job"
Pip:   [Links to quote via cross-screen workflow]
```

---

### 4E. Marketing

| Intent | Example Utterances | What Happens |
|--------|-------------------|--------------|
| `marketing.create_post` | "Create a Google post about the Campbelltown rewiring", "Post about that reno" | Multi-turn if missing params. `POST /api/marketing/gbp-post`. Shows draft, asks to post. |
| `marketing.insights` | "How's my local SEO?", "Search numbers?" | `GET /api/marketing/insights`. TTS summary. |
| `marketing.activity` | "Show me recent posts", "What have I posted?" | `GET /api/marketing/activity`. Shows list. |

**Multi-turn example -- `marketing.create_post`:**
```
Steve: "Chuck up a Google post"
Pip:   "Sure thing. What was the job?"
Steve: "Full bathroom reno, ripped out the old shower and retiled"
Pip:   "Nice. Which suburb?"
Steve: "Campbelltown"
Pip:   "Here's the draft:

        'Just wrapped up a full bathroom transformation in Campbelltown!
         Old shower out, fresh tiles in. The client wanted a modern look
         and we delivered. Need a bathroom refresh? Give us a call.'

        Want me to post it?"
Steve: "Yeah go for it"
Pip:   "Posted. Should show up on your Google Business Profile within the hour."
```

---

### 4F. Instructions

| Intent | Example Utterances | What Happens |
|--------|-------------------|--------------|
| `instructions.list` | "What rules do I have?", "Show my instructions" | `GET /api/instructions`. TTS count + category summary. |
| `instructions.add` | "New rule: always be casual in emails", "Add instruction: never use the word furthermore" | Auto-infers category. `POST /api/instructions`. Confirmation required. |
| `instructions.delete` | "Delete the last instruction", "Remove the formal language one" | Fuzzy-match by keyword. `DELETE`. Confirmation required. |

**Category auto-inference:**
- "Always be casual" -> category: `tone`
- "Never email suppliers on weekends" -> category: `workflow`
- "Flag anything over 10 grand" -> category: `priority`
- "Use metric, not imperial" -> category: `style`
- "Always mention warranty" -> category: `compliance`

**Example flow -- `instructions.add`:**
```
Steve: "New rule: keep emails under 3 sentences"
Pip:   "Adding instruction: 'Keep emails under 3 sentences',
        category: style. Save it?"
Steve: "Yeah"
Pip:   "Saved. Pip will follow this from now on."
```

---

### 4G. Construction (3 Tabs)

This is the densest workflow screen. The `metadata.tab_index` tells the router which sub-context applies (0=Leads, 1=Quotes, 2=Payments).

#### Leads Tab (tab_index=0)

| Intent | Example Utterances | What Happens |
|--------|-------------------|--------------|
| `construction.lead.create` | "Create a lead for John, bathroom reno in Penrith, budget 8k" | Multi-turn if params missing. `POST /api/construction/leads`. |
| `construction.lead.list` | "Show me all leads", "What's new?" | `GET /api/construction/leads`. TTS count. |
| `construction.lead.detail` | "Tell me about the Penrith lead" | Fuzzy-match by location/name. TTS reads details. |
| `construction.lead.update` | "Mark the Penrith lead as contacted" | `PATCH /api/construction/leads/{id}`. Confirmation required. |
| `construction.lead.extract` | "Extract a lead from that last email" | `POST /api/construction/leads/extract`. Creates lead from email AI. |

**Multi-turn example -- `construction.lead.create`:**
```
Steve: "New lead"
Pip:   "What's the client's name?"
Steve: "Dave Wilson"
Pip:   "What kind of job?"
Steve: "Kitchen renovation"
Pip:   "Where?"
Steve: "Penrith"
Pip:   "Budget estimate?"
Steve: "About 15 grand"
Pip:   "Got it. Dave Wilson, kitchen reno in Penrith, $15k budget.
        Save this lead?"
Steve: "Save it"
Pip:   "Lead saved. Want to create a quote for Dave?"
Steve: "Not yet"
```

**One-shot example (all params in one utterance):**
```
Steve: "Create a lead for Sarah Chen, bathroom reno in Campbelltown,
        budget 8 grand, urgent"
Pip:   "Lead: Sarah Chen, bathroom reno, Campbelltown, $8k, urgent.
        Save it?"
Steve: "Yeah"
Pip:   "Saved."
```

#### Quotes Tab (tab_index=1)

| Intent | Example Utterances | What Happens |
|--------|-------------------|--------------|
| `construction.quote.create` | "Generate a quote for the Penrith job", "Chuck a quote together for lead 5" | Multi-turn for costs. `POST /api/construction/quotes`. |
| `construction.quote.list` | "Show me all quotes", "What's pending?" | `GET /api/construction/quotes`. TTS summary. |
| `construction.quote.detail` | "What's the total on the Penrith quote?" | Fuzzy-match. TTS reads breakdown. |
| `construction.quote.update` | "They accepted the Campbelltown quote", "Mark quote 3 as sent" | `PATCH /api/construction/quotes/{id}`. Confirmation. |
| `construction.quote.followup` | "Draft a follow-up for that Penrith quote" | `POST /api/construction/quotes/{id}/tradie-followup`. TTS reads draft. |
| `construction.quote.invoice` | "Bang out an invoice for quote 3" | Generates invoice via invoice engine. Shows PDF. |

**Multi-turn example -- `construction.quote.create`:**
```
Steve: "Create a quote"
Pip:   "Which lead is this for?"
Steve: "The bloke in Penrith, the bathroom one"
Pip:   "Got it -- Dave Wilson, bathroom reno in Penrith. Materials cost?"
Steve: "About 2 grand"
Pip:   "Labor?"
Steve: "3 days, so call it 1800"
Pip:   "Standard 20% markup?"
Steve: "Yeah"
Pip:   "Quote total: $4,560. Materials $2,000 + labor $1,800 + 20% markup.
        Save it?"
Steve: "Save it"
Pip:   "Quote saved. Want to send it to Dave?"
```

#### Payments Tab (tab_index=2)

| Intent | Example Utterances | What Happens |
|--------|-------------------|--------------|
| `construction.payment.record` | "Record a payment of $3000 for the Penrith job" | Fuzzy-match quote. `POST /api/construction/payments`. Confirmation. |
| `construction.payment.list` | "Who's paid?", "Show me payments" | `GET /api/construction/payments`. TTS summary. |
| `construction.payment.pipeline` | "What's the damage?", "How much outstanding?" | `GET /api/construction/pipeline`. TTS: revenue breakdown. |

**Example flow -- `construction.payment.record`:**
```
Steve: "Dave Wilson just paid 3 grand for the bathroom job"
Pip:   "Recording $3,000 payment from Dave Wilson against the
        Penrith bathroom quote ($4,560 total). That leaves $1,560
        outstanding. Confirm?"
Steve: "Confirmed"
Pip:   "Payment recorded."
```

---

### 4H. Settings

Minimal voice support. No destructive actions via voice.

| Intent | Example Utterances | What Happens |
|--------|-------------------|--------------|
| `settings.show` | "Show me settings" | Navigate to settings screen. |
| `settings.test_connection` | "Test the server connection" | `GET /api/status`. TTS: "Server's running, all good." or "Can't reach the server." |
| `settings.version` | "What version am I running?" | TTS: "BackPocket OS version 2.3." |

---

## 5. Cross-Screen Workflows

Compound intents that span multiple screens. The router detects these and orchestrates multi-step execution.

### 5A. Email to Lead (`cross.email_to_lead`)

```
Steve: "That email from John looks like a lead, extract it"

Flow:
1. Fuzzy-match "John" in pending_approvals (GET /api/mobile/pending)
2. Extract email content (subject + body)
3. POST /api/construction/leads/extract with email data
4. AI extracts: client_name, job_type, location, budget, urgency
5. Confirm extracted data with Steve
6. POST /api/construction/leads to create
7. Navigate to Construction > Leads tab, highlight new lead

Pip: "Extracted from John's email: Kitchen renovation in Parramatta,
      budget around $12k, medium urgency. Save as a lead?"
Steve: "Yeah save it"
Pip: "Lead created. Want to quote it?"
```

### 5B. Lead to Quote (`cross.lead_to_quote`)

```
Steve: "Create a lead for Dave and generate a quote"

Flow:
1. Multi-turn: collect lead params (name, job, location, budget)
2. POST /api/construction/leads -> get lead_id
3. Multi-turn: collect quote params (materials, labor, markup)
4. POST /api/construction/quotes with lead_id
5. Navigate to Construction > Quotes tab

Pip: "Lead saved for Dave. Now for the quote -- materials cost?"
```

### 5C. Quote to Invoice (`cross.quote_to_invoice`)

```
Steve: "The Penrith job is done, invoice them"

Flow:
1. Fuzzy-match quote by location "Penrith"
2. PATCH /api/construction/quotes/{id} -> status = "accepted"
3. Generate invoice via POST /api/invoice/generate
4. Show invoice PDF / offer to email

Pip: "Penrith bathroom quote marked as accepted. Invoice generated:
      $4,560 to Dave Wilson. Want me to email it?"
```

### 5D. Full Pipeline Report (`cross.full_report`)

```
Steve: "Give me the full rundown on the business"

Flow:
1. GET /api/status (emails)
2. GET /api/construction/pipeline (money)
3. GET /api/marketing/insights (growth)
4. Gemini generates natural language summary
5. TTS playback

Pip: "Here's your business snapshot:
      Inbox: 27 emails, 4 urgent, oldest is 2 days.
      Pipeline: $41,185 across 8 quotes. 2 accepted, 2 pending, 4 drafts.
      Payments: $22,950 received this month, $18,235 outstanding.
      Marketing: Local search up 22%, 3 pending review requests.
      Busiest suburb: Campbelltown with 4 active jobs."
```

### 5E. Quote Follow-up Email (`cross.quote_to_followup`)

```
Steve: "Follow up with the Campbelltown bloke about his quote"

Flow:
1. Fuzzy-match quote by location "Campbelltown"
2. POST /api/construction/quotes/{id}/tradie-followup
3. Show generated message
4. Offer to send via email

Pip: "Here's the follow-up for the Campbelltown rewiring quote to James T:

      'Hey James, just checking in on the rewiring quote I sent through.
       Happy to chat if you've got any questions. Got a few jobs coming up
       so keen to lock in a date if you're ready to go. Cheers!'

      Want me to send it?"
```

---

## 6. Multi-Turn Conversation State Machine

### Session States

```
  IDLE ──> CLASSIFYING ──> COLLECTING ──> CONFIRMING ──> EXECUTING ──> COMPLETE
   ^                          |    ^          |                           |
   |                          |    |          v                           |
   |                          +----+      CANCELLED                      |
   |                        (loop for                                    |
   |                       each param)                                   |
   +---------------------------------------------------------------------+
```

### Session Object

```json
{
  "session_id": "uuid-abc-123",
  "state": "COLLECTING",
  "intent": "construction.quote.create",
  "collected_params": {
    "lead_id": 5,
    "materials_cost": 2000
  },
  "missing_params": ["labor_cost", "markup_percent"],
  "next_question": "How much for labor?",
  "defaults": {
    "markup_percent": 20
  },
  "last_entity": {
    "type": "lead",
    "id": 5,
    "name": "Dave Wilson"
  },
  "created_at": "2026-04-17T09:30:00Z",
  "ttl": 300
}
```

### Parameter Collection Order

Each intent defines a natural conversational order for collecting missing params:

| Intent | Param Order | Defaults |
|--------|------------|----------|
| `construction.lead.create` | client_name -> job_type -> location -> budget -> urgency -> email | urgency: "medium" |
| `construction.quote.create` | lead_id -> materials_cost -> labor_cost -> markup_percent | markup_percent: 20 |
| `construction.payment.record` | quote_id -> amount | -- |
| `marketing.create_post` | job_description -> suburb | -- |
| `instructions.add` | text -> category | category: auto-inferred |

### Context Carry-Forward

The `last_entity` field tracks the most recently created or viewed entity. When Steve says "that one," "the last one," or "it," the system resolves to `last_entity`.

```
Steve: "Create a lead for Dave, bathroom reno, Penrith, 8k"
Pip:   "Lead saved." [last_entity = {type: "lead", id: 12, name: "Dave"}]

Steve: "Now create a quote for that"
Pip:   [Resolves "that" -> last_entity -> lead_id: 12]
        "Quote for Dave's bathroom reno in Penrith. Materials cost?"
```

### Session Timeout

Sessions expire after 5 minutes of inactivity (`ttl: 300`). On expiry:
```
Pip: "We were working on a quote but it timed out. Want to start over?"
```

---

## 7. Confirmation & Safety

### Three Tiers

#### Tier A -- No Confirmation (read-only)

All read-only actions execute immediately: list, detail, summary, count, insights, navigation.

```
Steve: "Show me all leads"
Pip:   [Executes immediately, shows leads]
```

#### Tier B -- Verbal Confirmation (write actions)

Creating records, updating statuses, generating content. System reads back what it will do and waits for confirmation.

**Trigger words for YES:** "yes", "yeah", "yep", "do it", "go for it", "send it", "save it", "confirmed"
**Trigger words for NO:** "no", "nah", "cancel", "hold on", "wait", "stop"

```
Steve: "Create a lead for John, plumbing, Penrith"
Pip:   "Lead: John, plumbing job in Penrith, no budget set.
        Save it?"                                              <- Tier B
Steve: "Save it"
Pip:   "Saved."
```

#### Tier C -- Strong Confirmation (destructive/financial)

Sending real emails, batch approvals, recording payments, generating invoices, deleting records. System reads back specific details and requires a key phrase.

```
Steve: "Approve all tier 1 emails"
Pip:   "That's 4 emails to:
        - Sarah Mitchell (kitchen reno)
        - Dave Wilson (bathroom quote)
        - Priya S (electrical)
        - James T (roofing)
        Say 'send them all' to confirm."                       <- Tier C
Steve: "Send them all"
Pip:   "All 4 sent."
```

### Undo Capability

For write actions, store previous state in session. "Undo that" reverts within 60 seconds.

**Undoable:** Lead creation, quote creation, status updates, instruction additions.
**Not undoable:** Sent emails, recorded payments (flag as warning).

```
Steve: "Undo that"
Pip:   "Reverted: lead for Dave Wilson deleted."
```

---

## 8. Response Format

### When to Speak (TTS) vs Show UI vs Both

| Scenario | Speech | UI | Example |
|----------|--------|-----|---------|
| Summary/count queries | Yes | No | "You've got 27 emails, 4 urgent" |
| Confirmation prompts | Yes | Show confirmation card | "Send the email to Sarah?" |
| Navigation | No | Yes | Silently switch screen |
| List displays | No | Yes | Show filtered list |
| After creating record | Yes | Navigate + highlight | "Lead saved" + jump to leads tab |
| After approving email | Yes | Remove from list | "Email sent to Sarah" |
| After generating quote | Yes | Show quote detail | "Quote comes to $4,560" |
| After generating content | Yes | Show content | "Here's the GBP post: [reads]" |
| Errors | Yes | Show error toast | "That didn't work. Server's not responding." |

### Tone Guidelines

Responses match Steve's personality: Australian tradie, direct, no corporate speak.

| Don't Say | Say Instead |
|-----------|-------------|
| "Your email has been successfully dispatched to the recipient" | "Done, email's sent to Sarah." |
| "Lead creation completed with the following parameters" | "Sweet, lead saved. John, bathroom reno, Penrith, 8 grand." |
| "An error occurred during the processing of your request" | "Nah, that didn't work. Server's not responding." |
| "Would you like me to proceed with the operation?" | "Want me to go ahead?" |
| "I have identified 3 potential matches for your query" | "Found 3 options -- John, Dave, or Sarah?" |
| "The current pipeline valuation stands at $41,185" | "Pipeline's sitting at $41k." |

---

## 9. New Backend Endpoints

### New Routes (add to `routes/voice_commands.py`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/voice/command` | POST | Central voice command router -- receives transcript + context, returns classified intent + action result |
| `/api/voice/session` | POST | Create or retrieve voice session state for multi-turn |
| `/api/voice/session/{id}` | DELETE | Clear/expire a session |
| `/api/voice/confirm` | POST | Handle yes/no confirmation for pending actions |
| `/api/voice/intents` | GET | Return available intents for current screen (powers client-side suggestions) |

### Existing Endpoints Reused (no changes needed)

All current endpoints remain unchanged. The voice command router calls them internally:

- `GET/POST /api/mobile/pending`, `/api/mobile/approve`, `/api/mobile/chat`
- `GET/POST/PATCH /api/construction/leads`, `/quotes`, `/payments`, `/pipeline`
- `POST /api/construction/leads/extract`, `/quotes/{id}/tradie-followup`
- `GET/POST /api/documents`, `/api/documents/upload`, `/api/documents/analyze/{id}`
- `POST /api/marketing/gbp-post`, `GET /api/marketing/insights`, `/activity`
- `GET/POST /api/instructions`
- `POST /api/voice/transcribe` (existing Whisper transcription)
- `POST /api/voice/tts` (existing ElevenLabs)
- `POST /api/invoice/generate`
- `GET /api/status`
- `POST /api/revise`

---

## 10. New Files Required

### Backend (Python)

| File | Purpose |
|------|---------|
| `routes/voice_commands.py` | FastAPI router: `/api/voice/command`, `/confirm`, `/session`, `/intents` |
| `services/intent_classifier.py` | Gemini-based intent classification + entity extraction |
| `services/voice_session.py` | Session state machine for multi-turn conversations |
| `services/entity_resolver.py` | Fuzzy matching of entity references against live DB data |
| `services/voice_response.py` | Generate natural-language TTS responses from structured results |

### Flutter (Dart)

| File | Purpose |
|------|---------|
| `lib/services/voice_command_service.dart` | Full voice flow: record -> transcribe -> command -> handle response -> TTS |
| `lib/widgets/voice_fab.dart` | Global floating action button (mic icon) added to AppShell |
| `lib/widgets/voice_confirmation_card.dart` | UI card for confirming voice actions |
| `lib/models/voice_command_response.dart` | Dart model for `/api/voice/command` response |

### Flutter Modifications (existing files)

| File | Change |
|------|--------|
| `lib/main.dart` | Add `VoiceFab` widget to `AppShell` scaffold, pass screen context |
| `lib/screens/voice_input_screen.dart` | Replace stubbed `AudioRecorder` with real mic recording |
| `lib/services/api_service.dart` | Add `sendVoiceCommand()`, `confirmVoiceAction()`, `getVoiceIntents()` methods |

---

## 11. Error Handling

| Error | User Experience |
|-------|----------------|
| **Transcription fails** (Whisper/Ollama down) | TTS: "Sorry, didn't catch that. Try again?" Fall back to text input dialog. |
| **Low confidence** (< 0.4) | TTS: "Not sure what you mean. Can you say that differently?" |
| **Medium confidence** (0.4-0.7) | TTS: "Did you mean [option A] or [option B]?" Present top 2-3 intents. |
| **Wrong screen context** | Auto-navigate first. TTS: "Let me take you to Construction first..." then execute. |
| **Fuzzy match: multiple results** | TTS: "Found 3 leads in Penrith. Did you mean John, Dave, or Sarah?" |
| **Fuzzy match: zero results** | TTS: "Couldn't find any leads in Penrith. Want to create one?" |
| **Backend API error** | TTS: "That didn't work -- [error]. Want to try again?" |
| **Session expired** | TTS: "We were working on a quote but it timed out. Start over?" |
| **No internet / server down** | TTS: "Can't reach the server. Check your connection in Settings." |
| **Permission denied** (mic access) | Show system dialog. TTS fallback to text input. |

---

## 12. Implementation Phases

### Phase 1: Foundation (Week 1)

**Goal:** Voice works end-to-end for 5 core intents.

- [ ] Fix Flutter audio recording (replace stub in `voice_input_screen.dart` with real `flutter_sound` recorder)
- [ ] Build `routes/voice_commands.py` with `POST /api/voice/command`
- [ ] Build `services/intent_classifier.py` using Gemini 2.5-flash
- [ ] Implement 5 starter intents:
  - `dashboard.summary`
  - `inbox.list`
  - `inbox.approve` (with confirmation)
  - `construction.lead.list`
  - `navigate.screen`
- [ ] Add global voice FAB to `AppShell` in `main.dart`
- [ ] Build `lib/services/voice_command_service.dart`
- [ ] Test: speak "what's going on today" -> hear summary via TTS

### Phase 2: Core Workflows (Week 2)

**Goal:** Multi-turn works. Construction workflows complete.

- [ ] Build `services/voice_session.py` for multi-turn state machine
- [ ] Build `services/entity_resolver.py` for fuzzy matching
- [ ] Implement all Construction intents:
  - `construction.lead.create` (multi-turn)
  - `construction.quote.create` (multi-turn)
  - `construction.payment.record`
  - `construction.quote.followup`
  - `construction.quote.invoice`
- [ ] Implement confirmation flow (Tier B + Tier C)
- [ ] Add TTS responses via existing ElevenLabs endpoint
- [ ] Build `lib/widgets/voice_confirmation_card.dart`
- [ ] Test: speak "create a quote" -> multi-turn param collection -> save

### Phase 3: Full Coverage (Week 3)

**Goal:** All intents work across all screens.

- [ ] Implement remaining per-screen intents:
  - All Inbox intents (approve_batch, revise_draft, read_email)
  - All Documents intents
  - All Marketing intents
  - All Instructions intents
- [ ] Build cross-screen workflows (email_to_lead, lead_to_quote, quote_to_invoice, full_report)
- [ ] Build `services/voice_response.py` for natural response generation
- [ ] Implement batch operations (inbox.approve_batch)
- [ ] Implement undo capability
- [ ] Test: full end-to-end workflow -- email -> lead -> quote -> invoice via voice only

### Phase 4: Polish (Week 4)

**Goal:** Production-ready voice UX.

- [ ] Tradie slang tuning (iterate on classification prompt with real test utterances)
- [ ] Response tone calibration (ensure casual, not corporate)
- [ ] Edge case handling (ambiguous commands, mid-sentence corrections)
- [ ] Performance optimization:
  - Cache intent taxonomy in classification prompt
  - Pre-warm Gemini connection
  - Parallelize entity resolution + intent classification
- [ ] Wake word exploration (optional: "Hey Pip" hands-free activation)
- [ ] Add voice input animation/feedback to FAB (waveform visualizer)
- [ ] Accessibility: ensure voice commands supplement, not replace, touch UI
- [ ] Load testing: verify latency < 3s for full voice -> action -> response cycle

---

## Appendix A: Voice Command Quick Reference Card

For Steve's phone wallpaper / laminated workshop card:

```
DASHBOARD
  "What's going on today?"          -> Full business summary
  "How many emails?"                -> Pending count
  "What's my pipeline?"             -> Revenue numbers

INBOX
  "Show me urgent emails"           -> Filter tier 1
  "Approve the email to [name]"     -> Send draft (confirms first)
  "Read me [name]'s email"          -> TTS reads email + draft
  "Make it more casual"             -> Revise last viewed draft

CONSTRUCTION
  "New lead: [name], [job], [suburb], [budget]"    -> Create lead
  "Create a quote for the [suburb] job"            -> Multi-turn quote
  "They accepted the [suburb] quote"               -> Update status
  "Record $[amount] payment from [name]"           -> Log payment
  "What's the damage?"                             -> Pipeline total

DOCUMENTS
  "Scan a document"                 -> Open camera
  "What does this receipt say?"     -> AI analysis

MARKETING
  "Post about the [suburb] [job]"   -> Draft GBP post

ANYTIME
  "Hey Pip, [anything]"            -> Ask the AI assistant
  "Undo that"                      -> Revert last action (60s window)
  "Go to [screen]"                 -> Navigate
```

---

## Appendix B: Existing Endpoints Reference

All endpoints the voice command router dispatches to internally. These already exist and require no modifications.

| Endpoint | Method | Screen |
|----------|--------|--------|
| `/api/status` | GET | Dashboard |
| `/api/workflow/stages` | GET | Dashboard |
| `/api/mobile/pending` | GET | Inbox |
| `/api/mobile/approve` | POST | Inbox |
| `/api/mobile/chat` | POST | Chat |
| `/api/documents` | GET | Documents |
| `/api/documents/upload` | POST | Documents |
| `/api/documents/analyze/{id}` | POST | Documents |
| `/api/marketing/insights` | GET | Marketing |
| `/api/marketing/activity` | GET | Marketing |
| `/api/marketing/gbp-post` | POST | Marketing |
| `/api/instructions` | GET/POST | Instructions |
| `/api/construction/leads` | GET/POST | Construction |
| `/api/construction/leads/{id}` | GET/PATCH | Construction |
| `/api/construction/leads/extract` | POST | Construction |
| `/api/construction/quotes` | GET/POST | Construction |
| `/api/construction/quotes/{id}` | GET/PATCH | Construction |
| `/api/construction/quotes/{id}/tradie-followup` | POST | Construction |
| `/api/construction/pipeline` | GET | Construction |
| `/api/construction/payments` | GET/POST | Construction |
| `/api/voice/transcribe` | POST | Voice layer |
| `/api/voice/tts` | POST | Voice layer |
| `/api/invoice/generate` | POST | Vision Chat |
| `/api/revise` | POST | Inbox |

---

*Last Updated: 2026-04-17*
*Author: BackPocket OS Engineering*
*Status: Specification Complete -- Implementation follows 4-week phased rollout*
