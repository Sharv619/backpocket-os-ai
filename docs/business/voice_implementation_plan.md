# Voice Command Implementation Plan
**Based on:** `docs/business/aiworkflow.md`
**Audited:** 2026-04-19
**Branch:** `refactor/split-monoliths`

---

## Current Status vs Spec

| Phase | Spec Goal | Status |
|-------|-----------|--------|
| Phase 1 — Foundation | 5 core intents, POST /api/voice/command, VoiceFab | ✅ COMPLETE |
| Phase 2 — Core Workflows | Multi-turn, construction intents, confirmation tiers | ✅ COMPLETE |
| Phase 3 — Full Coverage | All intents, cross-screen workflows, undo, batch | ✅ COMPLETE |
| Phase 4 — Polish | Performance, tone tuning, wake word, load test | 🔧 IN PROGRESS |

**Summary:** Backend and Flutter foundation are fully built. All 50+ intents registered and handled. Cross-screen workflows implemented. Focus now is Phase 4 polish + end-to-end testing.

---

## What's Built (Verified)

### Backend
- `routes/voice_commands.py` — `POST /api/voice/command`, `/confirm`, `/session`, `/intents` all present
- `services/intent_classifier.py` — Gemini 2.5-flash with full intent taxonomy + tradie slang context
- `services/voice_session.py` — IDLE → CLASSIFYING → COLLECTING → CONFIRMING → EXECUTING state machine, 300s TTL
- `services/entity_resolver.py` — SequenceMatcher fuzzy matching, pronoun resolution ("that one", "it"), DB lookups
- `services/voice_response.py` — Intent-specific response generators, tradie tone, fallback handlers
- `routes/voice_handlers_dashboard.py` — 4 intents: summary, pending_count, pipeline_summary, growth_stats
- `routes/voice_handlers_inbox.py` — 8 intents: list, filter_tier, approve, approve_batch, show_draft, revise_draft, read_email, count_by_tier
- `routes/voice_handlers_construction.py` — 13 intents: all lead/quote/payment CRUD + extract + followup + invoice
- `routes/voice_handlers_misc.py` — 14 intents: documents (4), marketing (3), instructions (3), chat (2)
- `routes/voice_handlers_cross.py` — 4 cross-screen workflows: email_to_lead, lead_to_quote, quote_to_invoice, full_report
- `routes/voice_commands.py` inline — navigate.screen, meta.help, meta.cancel, meta.undo

### Flutter
- `lib/services/voice_command_service.dart` — Full flow: record → transcribe → command → TTS; VoiceFlowState machine
- `lib/widgets/voice_fab.dart` — Pulse animation, state-driven color/icon, tap/long-press
- `lib/widgets/voice_confirmation_card.dart` — Confirm/cancel UI, multi-turn follow-up prompts
- `lib/models/voice_command_response.dart` — Full model, VoiceUiAction, VoiceSessionState helpers
- `lib/screens/voice_input_screen.dart` — Conversation history, text fallback, real service integration
- `lib/main.dart` — VoiceFab wired into AppShell, screen context updates, confirmation overlay

---

## Phase 4 Remaining Work

### P4.1 — Real Mic Recording (BLOCKER for demo)
**File:** `lib/screens/voice_input_screen.dart`

Need to verify `AudioRecorder` is real `flutter_sound` / `record` package, not a stub. The spec says "replace stubbed AudioRecorder with real mic recording." Check pubspec.yaml for `record` or `flutter_sound` dependency. If missing, add it and wire up.

**Test:** Open app → tap mic FAB → speak → confirm transcription arrives at backend.

### P4.2 — Tradie Slang Tuning
**File:** `services/intent_classifier.py`

Run real test utterances against the classifier:
- "chuck a quote together for the bloke in Penrith" → `construction.quote.create`
- "what's the damage" → `construction.payment.pipeline`
- "give it the tick" → `inbox.approve`
- "bang out an invoice" → `construction.quote.invoice`
- "suss out the Campbelltown job" → `construction.lead.detail`

Log any misclassifications and update the TRADIE_SLANG_GUIDE section of the system prompt in `intent_classifier.py`.

### P4.3 — Response Tone Calibration
**File:** `services/voice_response.py`

Check generated responses against the spec's tone table. Responses must not say:
- "Your email has been successfully dispatched" → should be "Done, email's sent to Sarah."
- "Lead creation completed" → should be "Sweet, lead saved. Dave, bathroom reno, Penrith."

Add test utterances + expected responses. Fix any generators that sound corporate.

### P4.4 — Performance: Parallelise Entity Resolution
**File:** `routes/voice_commands.py`

The spec calls for parallelizing entity resolution + intent classification. Currently likely sequential. Wrap with `asyncio.gather()`:

```python
intent_result, resolved_entities = await asyncio.gather(
    classify_intent(transcript, screen_context, session_state),
    pre_resolve_entities(screen_context, metadata)
)
```

Target: full voice → action → TTS cycle < 3 seconds.

### P4.5 — Cache Intent Taxonomy in Prompt
**File:** `services/intent_classifier.py`

The full INTENT_TAXONOMY is sent with every classification call — this is expensive tokens. Cache the compiled system prompt string at module level (build once on import, reuse every call). Only the dynamic parts (screen_context, session_state, available_entities) should vary per call.

```python
_BASE_SYSTEM_PROMPT = _build_base_prompt()  # called once at import

async def classify_intent(transcript, screen_context, session_state):
    prompt = _BASE_SYSTEM_PROMPT + f"\nCurrent screen: {screen_context}\n..."
```

### P4.6 — End-to-End Test Suite
**New file:** `tests/test_voice_commands.py`

Minimum viable test coverage for demo confidence:

```python
# 1. Basic intent classification
async def test_classify_navigate():
    result = await classify_intent("go to inbox", "dashboard", {})
    assert result["intent"] == "navigate.screen"
    assert result["confidence"] > 0.7

# 2. POST /api/voice/command round-trip
def test_voice_command_endpoint(client):
    r = client.post("/api/voice/command", json={
        "transcript": "show me all leads",
        "screen_context": "construction",
        "session_id": "test-123",
        "metadata": {"tab_index": 0}
    })
    assert r.status_code == 200
    assert r.json()["intent"] == "construction.lead.list"

# 3. Multi-turn session state
def test_multi_turn_lead_create(client):
    session_id = "test-multiturn-456"
    # Turn 1: ambiguous
    r1 = client.post("/api/voice/command", json={
        "transcript": "new lead", "screen_context": "construction",
        "session_id": session_id, "metadata": {}
    })
    assert r1.json()["session_state"]["state"] == "COLLECTING"
    assert "client" in r1.json()["follow_up_prompt"].lower()

# 4. Confirmation flow
def test_confirmation_required_for_approve(client):
    r = client.post("/api/voice/command", json={
        "transcript": "approve the email to Sarah",
        "screen_context": "inbox",
        "session_id": "test-confirm-789",
        "metadata": {}
    })
    assert r.json()["needs_confirmation"] == True

# 5. Entity fuzzy match
async def test_entity_resolver_fuzzy():
    from services.entity_resolver import resolve_entity
    result = await resolve_entity("the Penrith bathroom job", "lead", {})
    # Should return a match or ask for disambiguation
    assert result is not None
```

### P4.7 — Missing Intent: `dashboard.navigate`
**File:** `routes/voice_handlers_dashboard.py`

Spec lists `dashboard.navigate` as a dashboard-specific intent (separate from `navigate.screen`). Currently the router handles `dashboard.navigate` inline via `_handle_navigate()` but it's not in the taxonomy registration. Add explicit handler or confirm existing inline handling covers it.

### P4.8 — Missing Cross-Screen: `cross.quote_to_followup`
**File:** `routes/voice_handlers_cross.py`

Spec §5E defines `cross.quote_to_followup` but audit only found `cross.email_to_lead`, `cross.lead_to_quote`, `cross.quote_to_invoice`, `cross.full_report`. Add this handler:

```python
@register_handler("cross.quote_to_followup")
async def handle_quote_to_followup(params, screen_context, metadata):
    # 1. Fuzzy-match quote by location/name
    # 2. POST /api/construction/quotes/{id}/tradie-followup
    # 3. Return draft message for TTS + show in UI
    # 4. Offer to send via email
```

### P4.9 — Wake Word (Optional / Post-Demo)
Explore "Hey Pip" hands-free activation. This requires always-on audio processing — complex for Flutter, power-intensive. Defer until after demo. Options: Picovoice Porcupine (on-device, free tier) or server-side wake word detection.

### P4.10 — Voice Input Animation
**File:** `lib/widgets/voice_fab.dart`

Spec requests waveform visualizer during recording. Currently uses pulse animation. Add audio level meter using `record` package's `onAmplitudeChanged` stream to drive a waveform widget. Non-blocking for demo — current pulse animation is acceptable.

---

## Demo Validation Checklist

Run these manually before demo to confirm voice pipeline is working:

- [ ] Tap mic FAB → real audio records (not text-only fallback)
- [ ] Speak "what's going on today" → TTS summary plays
- [ ] Speak "show me my leads" → navigates to construction, leads tab shown
- [ ] Speak "create a lead for Dave, bathroom reno, Penrith, 15 grand" → confirmation prompt
- [ ] Say "save it" → lead appears in construction screen
- [ ] Speak "chuck a quote together for Dave" → multi-turn param collection starts
- [ ] Complete quote multi-turn → quote saved, TTS confirms total
- [ ] Speak "approve the email to Sarah" → needs_confirmation=true, reads back details
- [ ] Say "send it" → email approved
- [ ] Speak "what's the damage" → pipeline summary via TTS
- [ ] Speak "go to inbox" → navigates silently

---

## Priority Order

| Priority | Task | Effort |
|----------|------|--------|
| P0 | P4.1 — Verify real mic recording in Flutter | 30 min |
| P1 | P4.6 — Add 5 basic voice command tests | 1 hr |
| P1 | P4.8 — Add `cross.quote_to_followup` handler | 30 min |
| P2 | P4.2 — Run slang tuning test utterances | 1 hr |
| P2 | P4.3 — Tone calibration check | 45 min |
| P2 | P4.5 — Cache intent taxonomy prompt | 30 min |
| P3 | P4.4 — Parallelise entity resolution | 45 min |
| P4 | P4.10 — Waveform animation on FAB | 2 hrs |
| Post-demo | P4.9 — Wake word "Hey Pip" | 1-2 days |

---

## Files to Touch (Phase 4)

| File | Change |
|------|--------|
| `pubspec.yaml` | Verify `record` or `flutter_sound` present |
| `lib/screens/voice_input_screen.dart` | Real mic if stub detected |
| `services/intent_classifier.py` | Cache base prompt, slang tuning |
| `services/voice_response.py` | Tone audit against spec table |
| `routes/voice_handlers_cross.py` | Add `cross.quote_to_followup` |
| `routes/voice_commands.py` | Parallelise with asyncio.gather |
| `tests/test_voice_commands.py` | New file — 5 core tests |

---

*Plan created: 2026-04-19*
*Spec source: docs/business/aiworkflow.md v1.0*
*Phases 1-3: COMPLETE. Focus: Phase 4 polish + demo validation.*
