# Skills Matrix — BackPocket MVP

> What the system can do today vs what's planned.
> Last updated: 2026-04-18

---

## Backend Skills (Python/FastAPI)

### Email Management
| Skill | Status | Endpoint | Notes |
|-------|--------|----------|-------|
| Gmail OAuth multi-account | Done | `/api/gmail/authenticate` | Supports 3+ accounts |
| Inbox polling (5-min cycle) | Done | `services/background.py` | Auto-triage T1-T5 |
| AI draft generation | Done | `services/gemini.py` | OpenRouter + Gemini fallback |
| Draft approve + send | Done | `POST /api/approve` | Multi-account token routing |
| Draft revise with AI | Done | `POST /api/revise` | Feedback-driven refinement |
| Batch archive | Done | `POST /api/archive` | Portal update detection |
| Email search (semantic) | Done | `POST /api/search-emails` | `services/email_memory.py` |
| Sender-specific rules | Done | `/api/sender-instruction*` | Per-sender AI instructions |

### Construction Pipeline
| Skill | Status | Endpoint | Notes |
|-------|--------|----------|-------|
| Lead CRUD | Done | `/api/construction/leads` | Create, list, get, update |
| AI lead extraction from email | Done | `POST /api/construction/leads/extract` | Gemini-powered |
| Quote CRUD | Done | `/api/construction/quotes` | With line items support |
| Quote cost calculator | Done | `services/construction.py` | Materials + labor + markup |
| Tradie follow-up generator | Done | `POST .../tradie-followup` | Friendly tone, <60 words |
| Payment recording | Done | `/api/construction/payments` | Record + list |
| Pipeline summary | Done | `GET /api/construction/pipeline` | Revenue + counts |
| Workflow stages (9) | Done | `GET /api/workflow/stages` | Seeded in DB |
| Per-lead stage tracking | Planned | FC-1 | `workflow_stage` column |
| Stage auto-advance | Planned | FC-1 | Event-driven progression |
| Site visit CRUD | Planned | FC-7 | Table exists, no endpoints |
| Job file management | Planned | FC-7 | Table exists, no endpoints |

### Voice Command System
| Skill | Status | Endpoint | Notes |
|-------|--------|----------|-------|
| Intent classification (50+) | Done | `services/intent_classifier.py` | Gemini 2.5-flash |
| Multi-turn state machine | Done | `services/voice_session.py` | 6-state FSM |
| Entity resolution (fuzzy) | Done | `services/entity_resolver.py` | DB-backed matching |
| Voice response generation | Done | `services/voice_response.py` | Tradie tone |
| Dashboard handlers | Done | `routes/voice_handlers_dashboard.py` | 5 intents |
| Inbox handlers | Done | `routes/voice_handlers_inbox.py` | 8 intents |
| Construction handlers | Done | `routes/voice_handlers_construction.py` | 12 intents |
| Cross-screen handlers | Done | `routes/voice_handlers_cross.py` | 4 intents |
| Misc handlers | Done | `routes/voice_handlers_misc.py` | Navigation, help, undo |
| Speech-to-text (Whisper) | Done | `POST /api/voice/transcribe` | |
| Text-to-speech (ElevenLabs) | Done | `POST /api/voice/tts` | Male/female voices |

### AI / RAG
| Skill | Status | Location | Notes |
|-------|--------|----------|-------|
| Agentic RAG pipeline | Done | `services/agentic_rag.py` | ChromaDB vector DB |
| Three-twin system | Done | `services/gemini.py` | Accountant/Auditor/Admin |
| Correction learning | Done | `services/database.py` | corrections table |
| Document vision (invoices) | Done | `services/document_vision.py` | Image analysis |
| Blog/story generation | Done | `services/agentic_rag.py` | NarrativeBlogGenerator |
| Coach analysis | Done | `POST /api/coach/analyze` | Draft quality feedback |

### Integrations
| Skill | Status | Location | Notes |
|-------|--------|----------|-------|
| Google Sheets sync | Done | `services/google_sheets.py` | Activity + client master |
| Google Drive sync to RAG | Done | `services/drive_integration.py` | Folder → vector DB |
| WhatsApp notifications | Done | `services/whapi.py` | Buttons + text messages |
| Invoice PDF generation | Done | `services/invoice_engine.py` | Auto-numbering |
| GBP post generation | Done | `POST /api/marketing/gbp-post` | AI-powered local posts |
| Hooks system | Done | `/api/hooks` | Pre/post approval events |

---

## Flutter Skills (Mobile/Desktop)

### Screens Implemented
| Screen | File | Key Features |
|--------|------|-------------|
| Dashboard | `dashboard_screen.dart` | Greeting, pipeline stages, growth stats |
| Inbox | `inbox_screen.dart` | Pending list, tier colors, approve dialog |
| Twin Chat | `twin_chat_screen.dart` | Free-form AI chat, suggestions |
| Documents | `documents_screen.dart` | Upload, analyze, search |
| Marketing | `marketing_screen.dart` | GBP posts, activity log, insights |
| Instructions | `instructions_screen.dart` | CRUD business rules |
| Construction | `construction_screen.dart` | 3-tab: leads, quotes, payments |
| Settings | `settings_screen.dart` | Server URL, API key |
| Vision Chat | `vision_chat_screen.dart` | Camera + AI analysis |
| Voice Input | `voice_input_screen.dart` | Speech recording UI |
| Voice Help | `voice_help_screen.dart` | Voice command guide |

### Widgets Implemented
| Widget | File | Purpose |
|--------|------|---------|
| VoiceFab | `voice_fab.dart` | Global mic button with state animation |
| VoiceRecordingOverlay | `voice_recording_overlay.dart` | Waveform + speech bubbles |
| VoiceConfirmationCard | `voice_confirmation_card.dart` | Action confirm/cancel |

### Flutter Planned
| Feature | Focus Chain | Status |
|---------|-------------|--------|
| Workflow stage tracker widget | FC-1 | Planned |
| Lead extraction dialog | FC-3 | Planned |
| Pipeline revenue card | FC-6 | Planned |
| Quote line item editor | FC-2 | Planned |
| Tier filter chips | FC-4 | Planned |
| Batch approve mode | FC-4 | Planned |
| Voice TTS playback | FC-5 | Planned |
| Multi-turn voice UI | FC-5 | Planned |
| Site visit tab | FC-7 | Planned |
| File upload/gallery | FC-7 | Planned |

---

## MCP Orchestrator Skills

| Tool | Server | Purpose |
|------|--------|---------|
| search_leads | BackPocket Local | Find leads by status/type/budget |
| create_quote | BackPocket Local | Generate quote with pricing |
| get_quote_template | BackPocket Local | Job-type pricing templates |
| get_pipeline_summary | BackPocket Local | Pipeline status overview |
| record_payment | BackPocket Local | Log payment received |
| get_overdue_quotes | BackPocket Local | Follow-up reminders |
| get_job_patterns | BackPocket Local | Historical pricing data |
| get_client_history | BackPocket Local | Past jobs + preferences |
| calculate_job_distance | BackPocket Local | Google Maps distance |
| estimate_travel_time | BackPocket Local | Travel + calendar block |
| draft_follow_up_email | BackPocket Local | Email template generation |
| match_quote_to_email | BackPocket Local | Link emails to quotes |
| suggest_next_action | BackPocket Local | AI-recommended next step |
