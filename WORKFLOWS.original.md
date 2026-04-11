# BackPocket OS - Workflows

## Overview
Workflows are multi-step processes that coordinate multiple tasks to achieve specific outcomes. These are designed for vibecoding with MCP servers.

---

## Project Architecture Context

### Current System Flow
```
Email Sources (Gmail + IMAP) → Triage (Gemini) → Dashboard (Approval Queue) → User Action → Send (Gmail) + Notify (WhatsApp)
```

### Key Services
- **FastAPI Server**: `main.py` (60+ endpoints, 8000+ lines total)
- **Database**: SQLite (`backpocket.db`, 8+ tables)
- **AI**: Gemini 2.5 Flash + Ollama fallback
- **Integrations**: Gmail, Google Sheets, WhatsApp (WHAPI)

---

## Core Workflows

### 1. email-triage-flow

**Purpose**: Process incoming emails through the full triage pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Gmail     │───▶│   Gemini    │───▶│   Tier      │
│   Fetch     │    │   Triage    │    │   Classify  │
└─────────────┘    └─────────────┘    └─────────────┘
                                              │
                                              ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   WhatsApp  │◀───│   Dashboard │◀───│   Draft     │
│   Notify    │    │   Push      │    │   Generate  │
└─────────────┘    └─────────────┘    └─────────────┘
```

**Implementation**:
```python
# services/gemini.py - triage_email()
# services/gmail.py - fetch_unread_emails()
# main.py - /run-poll endpoint
```

**Steps**:
1. Fetch emails from all accounts (Gmail + IMAP)
2. Run Gemini triage on each email
3. Categorize by tier (1-5):
   - Tier 1: Urgent → Auto-draft + WhatsApp
   - Tier 2: Important → Draft for review
   - Tier 3: Standard → Auto-reply
   - Tier 4: Updates → Newsletter/archive
   - Tier 5: Spam → Auto-archive
4. Generate drafts for Tier 1-2
5. Push pending approvals to dashboard (`pending_approvals` table)
6. Send WhatsApp notification for urgent (Tier 1)
7. Log activity to Sheets

**Trigger**: Cron every 5 minutes or manual `/run-poll`

---

### 2. approval-flow

**Purpose**: Handle approve/revise commands from user (WhatsApp/Dashboard)

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Command   │───▶│   Validate  │───▶│   Execute   │
│   Receive   │    │   ref_id    │    │   Action    │
└─────────────┘    └─────────────┘    └─────────────┘
                                              │
                                              ▼
┌─────────────┐    ┌─────────────┐
│   WhatsApp  │◀───│   Gmail     │
│   Confirm   │    │   Send      │
└─────────────┘    └─────────────┘
```

**Implementation**:
```python
# main.py - /api/approve, /api/revise endpoints
# services/gmail.py - send_email()
# services/whapi.py - send_notification()
```

**Steps**:
1. Receive approve/revise command (WhatsApp webhook or Dashboard API)
2. Validate ref_id exists in `pending_approvals` table
3. **If approve**:
   - Send email via Gmail API (`services/gmail.py`)
   - Update status to 'approved'
   - Move to `action_history` table
   - Archive original email
4. **If revise**:
   - Queue for re-draft generation (Gemini)
   - Update status to 'revised'
   - Store feedback in `corrections` table
5. Log action to `action_history` table
6. Send confirmation via WhatsApp

**Endpoints**:
- `POST /api/approve` - Approve and send
- `POST /api/revise` - Revise with feedback

---

### 3. client-onboarding-flow

**Purpose**: Add new client to system from email

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Email     │───▶│   Extract   │───▶│   Sheets    │
│   Receive   │    │   Client    │    │   Add       │
└─────────────┘    └─────────────┘    └─────────────┘
                                              │
                                              ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Rules     │◀───│   Memory    │◀───│   Database  │
│   Create    │    │   Update    │    │   Insert    │
└─────────────┘    └─────────────┘    └─────────────┘
```

**Implementation**:
```python
# main.py - /api/add-client-from-email
# services/gemini.py - extract_client_info()
# services/google_sheets.py - add_client()
# services/database.py - add_sender_instruction()
```

**Steps**:
1. Receive new client email (manual trigger or AI detection)
2. Extract client details using Gemini (`extract_client_info`)
3. Add to Google Sheets (`Clients_Master` tab)
4. Create sender-specific instructions in `sender_instructions` table
5. Set up email rules for client
6. Generate welcome message template

**Endpoint**: `POST /api/add-client-from-email`

---

### 4. system-diagnostic-flow

**Purpose**: Run comprehensive system health check

```
┌─────────────┐
│   Start    │
│   Flow     │
└─────────────┘
      │
      ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Database │───▶│   Gemini   │───▶│   Gmail    │
│   Check    │    │   API      │    │   OAuth    │
└─────────────┘    └─────────────┘    └─────────────┘
      │
      ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   WhatsApp  │───▶│   Sheets   │───▶│   Generate  │
│   Webhook   │    │   API      │    │   Report   │
└─────────────┘    └─────────────┘    └─────────────┘
```

**Implementation**:
```python
# services/self_check.py - run_self_check()
# services/local_audit.py - run_self_audit()
# services/diagnostics.py - get_system_diagnostics()
```

**Steps**:
1. Check database connectivity (SQLite)
2. Test Gemini API connection
3. Verify Gmail OAuth tokens
4. Test WhatsApp webhook (send test message)
5. Check Sheets API
6. Review error logs (last 24h from `docs/ERROR_LOG.md`)
7. Generate health report

**Endpoints**:
- `GET /api/status` - Quick status
- `GET /api/audit` - Full audit
- `GET /self-check` - Diagnostic run

---

### 5. twin-chat-flow

**Purpose**: Handle conversational interaction with Twin AI

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   User     │───▶│   Twin     │───▶│   Memory    │
│   Message  │    │   Brain    │    │   Context   │
└─────────────┘    └─────────────┘    └─────────────┘
                                              │
                                              ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Database │◀───│   Gemini   │◀───│   Response  │
│   Save     │    │   Generate │    │   Render   │
└─────────────┘    └─────────────┘    └─────────────┘
```

**Implementation**:
```python
# main.py - /api/twin-chat endpoint
# services/twin_brain.py - get_twin_response()
# services/session_manager.py - save_conversation()
# services/memory.py - get_twin_context()
```

**Steps**:
1. Receive user message
2. Load Twin memory from `twin_memory` table
3. Load session context from `chat_conversations` table
4. Build prompt with instructions from `instructions` table
5. Generate response using Gemini
6. Save to conversation history
7. Check for actions to execute (`agreed_actions` table)
8. Return response with optional choices

**Endpoint**: `POST /api/twin-chat`

---

### 6. daily-reset-flow

**Purpose**: End-of-day cleanup and preparation

**Implementation**:
```python
# main.py - scheduled task (11pm)
# services/database.py - archive_approved()
# services/google_sheets.py - log_daily_summary()
```

**Steps**:
1. Archive all approved items from today
2. Generate daily summary:
   - Emails processed count
   - Tier breakdown (1-5 counts)
   - Time saved estimate
   - Actions taken
3. Send summary via WhatsApp
4. Backup database
5. Clear temp files
6. Schedule next day's tasks

---

### 7. backup-recovery-flow

**Purpose**: Restore from backup

**Implementation**:
```python
# scripts/backup_restore.ps1
# services/database.py - restore_from_backup()
```

**Steps**:
1. List available backups (`backups/` folder)
2. User selects backup
3. Stop server
4. Close SQLite connections
5. Copy backup to `backpocket.db`
6. Restart server
7. Verify integrity (run self-check)

---

## Workflow Triggers

| Workflow | Trigger | Frequency |
|----------|---------|-----------|
| email-triage-flow | Cron | Every 5 min |
| approval-flow | Webhook/API | On-demand |
| client-onboarding-flow | Manual/AI | On-demand |
| twin-chat-flow | User input | On-demand |
| system-diagnostic-flow | Cron + Manual | Daily + On-demand |
| daily-reset-flow | Cron | Daily (11pm) |
| backup-recovery-flow | Manual | On-demand |

---

## Error Handling

Each workflow includes:
- **Retry logic**: 3 attempts with exponential backoff
- **Fallback**: Alternate service if primary fails (e.g., Ollama if Gemini fails)
- **Rollback**: Revert partial changes on failure
- **Notification**: Alert user via WhatsApp on critical failure

**Example**:
```python
async def triage_with_retry():
    for attempt in range(3):
        try:
            return await run_triage()
        except Exception as e:
            if attempt == 2:
                await notify_error(f"Triage failed: {e}")
                raise
            await asyncio.sleep(2 ** attempt)  # exponential backoff
```

---

## Monitoring

```bash
# View workflow status
curl http://localhost:8000/api/status

# View pending approvals
curl http://localhost:8000/api/pending

# View action history
curl http://localhost:8000/api/history

# View error logs
cat docs/ERROR_LOG.md
```

---

## Workflow Implementation Pattern

```python
from services.workflow_engine import Workflow

email_triage = Workflow(
    name="email-triage-flow",
    steps=[
        Step("fetch_gmail", services.gmail.fetch_unread),
        Step("fetch_imap", services.imap.fetch_unread),
        Step("triage", services.gemini.batch_triage),
        Step("categorize", categorize_by_tier),
        Step("generate_drafts", services.gemini.draft_responses),
        Step("push_dashboard", services.database.push_pending),
        Step("notify", services.whapi.send_urgent),
        Step("log", services.sheets.log_activity),
    ],
    triggers=[CronTrigger("*/5 * * * *")],
    error_handling=ErrorHandling(
        retry=3,
        backoff="exponential",
        fallback=fallback_handler,
        alert=alert_handler
    )
)
```

---

## Best Practices

1. **Idempotency**: Each step should be safe to run multiple times
2. **Atomicity**: Group related changes in transactions
3. **Visibility**: Log every step with timestamps
4. **Timeout**: Set max execution time per workflow (30s default)
5. **Isolation**: Run heavy workflows in separate processes
6. **MCP Compliance**: 
   - Use Streamable HTTP transport
   - Tool descriptions under 50 words
   - Structured error responses
   - Input validation with JSON Schema

---

## Visual Workflow Diagram (ASCII)

### Complete System Flow
```
┌─────────────────────────────────────────────────────────────────────────┐
│                         BACKPOCKET OS WORKFLOW                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   EMAIL IN ───▶ TRIAGE ────▶ DRAFT ────▶ APPROVE ────▶ SEND            │
│                  │             │            │              │           │
│                  ▼             ▼            ▼              ▼           │
│              [GEMINI]      [DASHBOARD]  [USER]      [GMAIL API]        │
│                                                         │              │
│   ┌─────────────────────────────────────────────────────┼──────────┐  │
│   │                    NOTIFICATIONS                   │          │  │
│   │   WhatsApp: approve / revise / nudge / summary ◀───┘          │  │
│   └──────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   ═══════════════════════════════════════════════════════════════════   │
│                                                                         │
│   DATA SYNC:                                                            │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐        │
│   │  Gmail  │◀──▶│  Gemini  │◀──▶│ Database │◀──▶│  Sheets  │        │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘        │
│                                                                         │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐                        │
│   │  Twin   │◀──▶│  Memory  │◀──▶│ Sessions │                        │
│   │  Chat   │    └──────────┘    └──────────┘                        │
│   └──────────┘                                                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## File References

| Workflow | Key Files |
|----------|-----------|
| email-triage | `services/gemini.py`, `services/gmail.py`, main.py `/run-poll` |
| approval | `main.py` `/api/approve`, `/api/revise`, `services/gmail.py` |
| client-onboarding | `main.py` `/api/add-client-from-email`, `services/google_sheets.py` |
| diagnostics | `services/self_check.py`, `services/local_audit.py`, `main.py` `/api/audit` |
| twin-chat | `main.py` `/api/twin-chat`, `services/twin_brain.py`, `services/session_manager.py` |
| backup | `scripts/backup_restore.ps1`, `services/database.py` |