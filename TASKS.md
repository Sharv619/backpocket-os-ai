# BackPocket OS - Tasks
## Overview
Tasks are discrete, actionable items can be executed individually or as part of workflows. These are designed to work with MCP servers for vibecoding workflows.
---
## Project Structure (For Task Context)
### Main Files
- `main.py` - FastAPI app (~2450 lines, 60+ endpoints)
- `services/database.py` - SQLite operations (~650 lines)
- `services/gemini.py` - AI operations (~780 lines)
- `services/gmail.py` - Gmail API (~14KB)
- `services/google_sheets.py` - Sheets sync (~19KB)
- `services/whapi.py` - WhatsApp API (~15KB)
- `services/twin_brain.py` - Twin knowledge system
- `services/session_manager.py` - Session/memory
- `static/index.html` - Dashboard (~3400 lines)
- `backpocket.db` - SQLite database
### Scripts (40+ diagnostic scripts)
- `scripts/diag_*.py` - Various diagnostics
- `scripts/debug_*.py` - Debug utilities
- `scripts/setup_*.py` - Setup helpers
---
## Operational Tasks
### Email Operations
| Task | Description | Frequency |
|------|-------------|-----------|
| `triage-emails` | Run email triage on all accounts | Every 5 min |
| `nudge-clients` | Send nudges for pending replies | Hourly |
| `approve-draft` | Approve and send email draft | On-demand |
| `revise-draft` | Revise draft with feedback | On-demand |
| `search-emails` | Search emails by query | On-demand |
| `rescue-email` | Rescue email to inbox | On-demand |
### Data Sync
| Task | Description | Frequency |
|------|-------------|-----------|
| `sync-clients` | Sync client list from Sheets | Hourly |
| `sync-activity` | Log activity to Sheets | On-action |
| `refresh-priority` | Refresh priority list | Hourly |
| `sync-portal` | Sync portal updates | Every 30 min |
### Maintenance
| Task | Description | Frequency |
|------|-------------|-----------|
| `backup-db` | Backup SQLite database | Daily |
| `rotate-logs` | Clean old logs | Weekly |
| `cleanup-sessions` | Clean stale sessions | Hourly |
| `vacuum-db` | Optimize SQLite database | Weekly |
---
## Security Tasks
| Task | Description | Frequency |
|------|-------------|-----------|
| `audit-auth` | Audit API authentication | Weekly |
| `check-tokens` | Check OAuth token expiry | Daily |
| `scan-secrets` | Scan for exposed secrets | On push |
| `rate-limit-check` | Verify rate limiting | Monthly |
| `sanitize-input` | Validate/sanitize inputs | Per request |
| `check-webhook` | Verify webhook signatures | Per request |
---
## Development Tasks
### Quality Assurance
| Task | Description | Trigger |
|------|-------------|---------|
| `ruff-check` | Run linter | On save |
| `ruff-fix` | Auto-fix lint issues | On save |
| `mypy-check` | Run type checker | On save |
| `pytest` | Run test suite | Pre-deploy |
### Deployment
| Task | Description | Frequency |
|------|-------------|-----------|
| `deploy-server` | Deploy to production | Manual |
| `restart-server` | Restart FastAPI server | Manual |
| `rollback` | Rollback to previous | Emergency |
### Monitoring
| Task | Description | Frequency |
|------|-------------|-----------|
| `health-check` | Check all services | Every 5 min |
| `view-logs` | Tail recent logs | On-demand |
| `disk-usage` | Check disk space | Daily |
| `error-check` | Check error log | Hourly |
---
## Task Definitions
### triage-emails
```yaml
name: triage-emails
description: Run full email triage on all connected accounts
service: twin-email-server
tools:
- fetch_emails (Gmail)
- fetch_emails (IMAP)
steps:
1. Fetch emails from Gmail (primary)
2. Fetch emails from IMAP accounts
3. Run Gemini triage on each (services/gemini.py)
4. Categorize by tier (1-5)
5. Generate drafts for Tier 1-2
6. Push to pending_approvals table
7. Send WhatsApp for Tier 1 (services/whapi.py)
8. Log to Sheets (services/google_sheets.py)
```
### nudge-clients
```yaml
name: nudge-clients
description: Send automatic nudges to clients with pending approvals
service: twin-whatsapp-server
tools:
- send_notification
steps:
1. Query pending_approvals where last_nudge_at > 24h
2. For each, send WhatsApp reminder
3. Update last_nudge_at timestamp
4. Log nudge action
```
### sync-clients
```yaml
name: sync-clients
description: Sync client list from Google Sheets
service: twin-sheets-server
tools:
- sync_clients
- get_priority_list
steps:
1. Call get_client_emails from Sheets
2. Update whitelist cache in gemini.py
3. Extract domains for company shield
4. Log sync timestamp
```
### backup-db
```yaml
name: backup-db
description: Backup SQLite database to backups folder
service: twin-database-server
tools:
- export_db
steps:
1. Lock database
2. Copy to backups/backup_YYYYMMDD_HHMMSS.db
3. Prune backups older than 30 days
4. Log backup completion
```
### run-self-check
```yaml
name: run-self-check
description: Run system health check
service: twin-audit-server
tools:
- self_check
- local_audit
steps:
1. Check database connectivity
2. Test Gemini API
3. Verify Gmail OAuth tokens
4. Test WhatsApp webhook
5. Check Sheets API
6. Generate report
```
---
## API Task Endpoints
| Task | Endpoint | Method |
|------|----------|--------|
| triage-emails | `/run-poll` | GET |
| approve-draft | `/api/approve` | POST |
| revise-draft | `/api/revise` | POST |
| search-emails | `/api/search-emails` | POST |
| rescue-email | `/api/rescue` | POST |
| sync-clients | `/test-sheets` | GET |
| health-check | `/api/status` | GET |
| self-check | `/self-check` | GET |
| audit | `/api/audit` | GET |
---
## Task Execution
```bash
# Run triage
curl http://localhost:8000/run-poll
# Approve draft
curl -X POST http://localhost:8000/api/approve \
-H "Content-Type: application/json" \
-d '{"ref_id": "2026-04-00001"}'
# Run health check
curl http://localhost:8000/api/status
# Run self-check
curl http://localhost:8000/self-check
# Sync clients
curl http://localhost:8000/test-sheets
```
---
## Priority Matrix
| Priority | Tasks |
|----------|-------|
| Critical | triage-emails, approve-draft, send-draft |
| High | sync-clients, nudge-clients, run-self-check |
| Medium | backup-db, health-check, refresh-priority |
| Low | rotate-logs, cleanup-sessions, vacuum-db |
---
## Task Dependencies
```
triage-emails
├── twin-email-server (fetch_emails)
├── twin-ai-server (triage_email, draft_response)
├── twin-database-server (query_pending, log_action)
└── twin-whatsapp-server (send_notification)
approve-draft
├── twin-email-server (send_draft)
├── twin-database-server (update_status)
└── twin-whatsapp-server (send_notification)
sync-clients
├── twin-sheets-server (sync_clients, get_priority_list)
└── twin-ai-server (update_cache)
```
---
## Error Handling Per Task
| Task | Retry | Fallback | Alert |
|------|-------|----------|-------|
| triage-emails | 3x | Skip & log | WhatsApp |
| approve-draft | 3x | Keep pending | WhatsApp |
| sync-clients | 3x | Use cache | None |
| backup-db | 1x | Fail + alert | Email |
| run-self-check | 1x | Partial report | None |