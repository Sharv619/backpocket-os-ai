# BackPocket OS — OpenCode Orchestrator

## Overview

This document serves as the **Orchestrator** for BackPocket OS, integrating:
- **Skills** (`SKILLS.md`) - What the system can do
- **Workflow** (`workflow.md`) - How development happens
- **MCP Servers** - The execution layer for OpenCode

---

## Quick Start — Full Stack

```bash
# 1. Start MCP servers (required for OpenCode to work)
./scripts/mcp-start.sh

# 2. Start backend
source venv/bin/activate
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000

# 3. Open OpenCode (in a new terminal)
npx opencode
```

---

## Orchestrator Skills (From SKILLS.md)

The orchestrator exposes these skill groups to OpenCode:

### Skill Group 1: backpocket-mcp
| Command | Description | Use Case |
|---------|-------------|----------|
| `start` | Start all MCP servers | Initialize system |
| `stop` | Stop all MCP servers | Cleanup |
| `status` | Check server health | Diagnostics |
| `logs` | View recent logs | Debugging |
| `restart <server>` | Restart specific server | Fix issues |

### Skill Group 2: backpocket-email
| Command | Description | Use Case |
|---------|-------------|----------|
| `triage` | Run full email triage | Process inbox |
| `approve <ref_id>` | Approve and send draft | HITL workflow |
| `revise <ref_id>` | Revise with feedback | Improve drafts |
| `drafts` | List pending drafts | Review queue |

### Skill Group 3: backpocket-twin
| Command | Description | Use Case |
|---------|-------------|----------|
| `chat` | Start Twin chat session | AI conversation |
| `instructions` | Manage Twin instructions | Configure AI |
| `memory` | View/clear Twin memory | Reset context |
| `coach` | Run communication coach | Improve tone |

### Skill Group 4: backpocket-sync
| Command | Description | Use Case |
|---------|-------------|----------|
| `clients` | Sync client list | Update CRM |
| `activity` | Log to Sheets | Business OS |
| `priority` | Refresh priority list | Update queue |

---

## MCP Servers (Auto-Loaded via .mcp.json)

| Server | Port | Tools Available |
|--------|------|-----------------|
| **backpocket-leads** | 3100 | search_leads, get_lead, create_lead |
| **backpocket-quotes** | 3101 | create_quote, get_quote_template, list_quotes |
| **backpocket-pipeline** | 3102 | get_pipeline_summary, record_payment |
| **backpocket-knowledge** | 3103 | save_note, search_notes, list_notes |

---

## OpenCode Orchestrator Commands

When running `npx opencode` in this directory, you can:

### Navigation
- Ask: "Show me the leads MCP server code"
- Ask: "Show me the email workflow"

### Execution
- Ask: "Run the email triage skill"
- Ask: "Search for leads with status=new"

### Development
- Ask: "Add a new endpoint for X"
- Ask: "Fix the Flutter document upload"

### Troubleshooting
- Ask: "Why is the MCP server not starting?"
- Ask: "Check all server health"

---

## Common OpenCode Workflows

### 1. Development Flow
```bash
# Ask OpenCode to:
"Create a new feature: voice-to-quote"
```

### 2. Debug Flow
```bash
# Ask OpenCode to:
"The document upload is failing - check the logs"
```

### 3. Testing Flow
```bash
# Ask OpenCode to:
"Run the approval workflow test"
```

---

## Key Endpoints (For OpenCode Context)

| Endpoint | Purpose |
|----------|---------|
| `/api/mobile/pending` | Inbox with tier labels |
| `/api/mobile/approve` | Approve/reject workflow |
| `/api/voice/quote-from-transcript` | Voice-to-quote |
| `/api/construction/leads` | Lead CRUD |
| `/api/construction/quotes` | Quote CRUD |
| `/api/construction/payments` | Payment tracking |

---

## Critical Gotchas

1. **MCP servers must be running** before OpenCode can use them
2. **Backend needs restart** after changes to `main.py`
3. **Port 8000** must be free (check with `lsof -i:8000`)
4. **Flutter app** runs separately from backend

---

## Architecture

```
┌──────────────────────────────────────────────┐
│         OpenCode Orchestrator                │
│  (npx opencode + .mcp.json config)           │
├──────────────────────────────────────────────┤
│                                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│  │ Leads   │ │ Quotes  │ │Knowledge│        │
│  │ MCP     │ │  MCP    │ │  MCP    │        │
│  │ :3100   │ │  :3101  │ │  :3103  │        │
│  └────┬────┘ └────┬────┘ └────┬────┘        │
│       │          │          │              │
│       └──────────┴───────────┘              │
│                   │                         │
│            ┌─────┴─────┐                    │
│            │  Skills   │                    │
│            │  (SKILLS) │                    │
│            └───────────┘                    │
│                   │                         │
│            ┌──────┴──────┐                   │
│            │   Backend   │                   │
│            │  FastAPI    │                   │
│            │  main.py    │                   │
│            └─────────────┘                   │
└──────────────────────────────────────────────┘
```

---

**Document Updated:** 2026-04-14  
**For:** OpenCode orchestrator setup