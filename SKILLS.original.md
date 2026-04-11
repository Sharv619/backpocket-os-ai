# BackPocket OS - Skills

## Overview
Skills are discrete, reusable capabilities that can be invoked to perform specific tasks within the BackPocket OS ecosystem. These follow MCP (Model Context Protocol) best practices for vibecoding.

---

## Core Skills

### 1. backpocket-mcp
**Purpose**: Main MCP server management

| Command | Description |
|---------|-------------|
| `start` | Start all MCP servers |
| `stop` | Stop all MCP servers |
| `status` | Check server health |
| `logs` | View recent logs |
| `restart <server>` | Restart specific server |

**Files**: `main.py`, `services/gemini.py`, `services/database.py`

---

### 2. backpocket-email
**Purpose**: Email operations (Gmail + IMAP)

| Command | Description |
|---------|-------------|
| `triage` | Run full email triage |
| `approve <ref_id>` | Approve and send draft |
| `revise <ref_id>` | Revise draft with feedback |
| `search <query>` | Search emails |
| `rescue <ref_id>` | Rescue to inbox |
| `drafts` | List all pending drafts |

**Files**: `services/gmail.py`, `services/imap.py`, `services/gemini.py`

---

### 3. backpocket-twin
**Purpose**: Twin AI management

| Command | Description |
|---------|-------------|
| `chat` | Start Twin chat session |
| `instructions` | Manage Twin instructions |
| `memory` | View/clear Twin memory |
| `coach` | Run communication coach |
| `sops` | View/manage SOPs |

**Files**: `services/twin_brain.py`, `services/session_manager.py`, `services/memory.py`

---

### 4. backpocket-sync
**Purpose**: Google Sheets synchronization

| Command | Description |
|---------|-------------|
| `clients` | Sync client list from Sheets |
| `activity` | Log activity to Sheets |
| `priority` | Refresh priority list |
| `portal` | Sync portal updates |

**File**: `services/google_sheets.py`

---

### 5. backpocket-whatsapp
**Purpose**: WhatsApp (WHAPI) operations

| Command | Description |
|---------|-------------|
| `notify` | Send WhatsApp notification |
| `webhook` | Handle incoming webhook |
| `buttons` | Process button replies |

**File**: `services/whapi.py`

---

### 6. backpocket-audit
**Purpose**: System auditing

| Command | Description |
|---------|-------------|
| `full` | Run full system audit |
| `security` | Security audit only |
| `database` | Database integrity check |
| `api` | API endpoint validation |
| `export` | Export audit report |

**Files**: `services/local_audit.py`, `services/self_check.py`, `services/diagnostics.py`

---

## MCP Server Skills (For Vibecoding)

### 7. twin-database-server
**Purpose**: Database CRUD operations (SQLite)

**Tools**:
- `list_tables` - List all database tables
- `query_pending` - Get pending approvals
- `create_instruction` - Add new instruction
- `get_corrections` - Get user corrections
- `log_action` - Record action to history
- `get_sessions` - Get chat sessions

**Implementation**: `services/database.py`, `services/session_manager.py`

---

### 8. twin-email-server
**Purpose**: Gmail/IMAP integration

**Tools**:
- `fetch_emails` - Fetch from Gmail/IMAP
- `send_draft` - Send approved draft
- `search_emails` - Search messages
- `archive_email` - Archive message

**Implementation**: `services/gmail.py`, `services/imap.py`

---

### 9. twin-ai-server
**Purpose**: Gemini/Ollama AI operations

**Tools**:
- `triage_email` - Classify email tier (1-5)
- `draft_response` - Generate draft
- `analyze_tone` - Analyze communication style
- `extract_client` - Extract client info from email

**Implementation**: `services/gemini.py`

---

### 10. twin-sheets-server
**Purpose**: Google Sheets sync

**Tools**:
- `sync_clients` - Sync client list
- `log_activity` - Log to activity sheet
- `get_priority_list` - Fetch priority list

**Implementation**: `services/google_sheets.py`

---

### 11. twin-whatsapp-server
**Purpose**: WhatsApp notifications

**Tools**:
- `send_notification` - Send WhatsApp message
- `handle_webhook` - Process incoming messages
- `handle_buttons` - Handle button replies (approve/revise)

**Implementation**: `services/whapi.py`

---

### 12. twin-audit-server
**Purpose**: System diagnostics

**Tools**:
- `self_check` - Run system health check
- `local_audit` - Run comprehensive audit
- `get_diagnostics` - Get system diagnostics

**Implementation**: `services/local_audit.py`, `services/self_check.py`

---

## Skill Configuration

### Environment Variables
```bash
# Required for all skills
GEMINI_API_KEY=your_key_here
SPREADSHEET_ID=your_spreadsheet_id
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
WHAPI_TOKEN=your_whapi_token
FOUNDER_PHONE=+1234567890

# Optional
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest
OPENROUTER_API_KEY=your_key
```

---

## Skill Invocation Examples

```bash
# Start MCP servers
backpocket-mcp start

# Run triage
backpocket-email triage

# Chat with Twin
backpocket-twin chat

# Run audit
backpocket-audit full

# Sync clients
backpocket-sync clients
```

---

## Implementation Notes

- Skills follow single responsibility principle
- Each skill has clear input/output contracts
- Use environment variables for configuration
- Implement proper error handling per skill
- Add health check endpoints for monitoring
- Use Streamable HTTP transport for production
- Implement rate limiting per skill
- Add output sanitization for security

---

## MCP Best Practices Applied

1. **Tool descriptions**: Clear, verbose descriptions under 50 words
2. **Input validation**: JSON Schema for all tool inputs
3. **Error handling**: Structured errors with `isError: true`
4. **Versioning**: Semantic versioning for each server
5. **Security**: OAuth 2.1, input sanitization, rate limiting