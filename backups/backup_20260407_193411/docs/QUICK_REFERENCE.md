# BackPocket OS - Quick Reference

## Dashboard URLs
| Feature | URL |
|---------|-----|
| Main Dashboard | http://localhost:8000/dashboard |
| Pending Emails | http://localhost:8000/api/pending |
| History | http://localhost:8000/api/history |
| Corrections | http://localhost:8000/api/corrections |
| Twin Instructions | http://localhost:8000/api/sender-instructions |
| Debug Draft | http://localhost:8000/api/debug-draft/<ref_id> |
| System Status | http://localhost:8000/api/status |

---

## WhatsApp Commands
| Command | Action |
|---------|--------|
| `approve <ref>` | Send the draft |
| `revise <ref>: feedback` | Revise with feedback |
| `pending` | See waiting emails |
| `self-check` | Run diagnostics |

---

## Tier Rules

| Tier | Description | Action |
|------|-------------|--------|
| 1 | Existing clients | Stay in inbox, needs draft |
| 2 | Govt/Assoc (ATO, ASIC) | Stay in inbox, log only |
| 3 | Suppliers | Archive |
| 4 | Portal Digests | Log + Archive |

---

## Key Files

| File | Purpose |
|------|---------|
| main.py | FastAPI server |
| .env | API credentials |
| backpocket.db | SQLite database |
| static/index.html | Dashboard UI |
| services/gemini.py | AI (triage, drafting) |
| services/gmail.py | Email handling |
| services/google_sheets.py | Sheets API |
| services/whapi.py | WhatsApp |

---

## Batch Files

| File | Purpose |
|------|---------|
| LAUNCH_BACKPOCKET_TWIN.bat | Start server (console) |
| LAUNCH_BACKPOCKET_OS.bat | Start server + open browser |
| RESTART_SERVER.bat | Restart server |
| SETUP_AUTOSTART.bat | Setup auto-start on boot |
| RUN_DIAGNOSTICS.bat | Check system health |

---

## API Endpoints

### Email
- `GET /api/pending` - List pending emails
- `POST /api/approve` - Send draft
- `POST /api/revise` - Revise draft
- `POST /api/save-draft` - Save draft edits
- `POST /api/add-client-from-email` - Extract client to Sheets

### Twin Learning
- `GET /api/sender-instructions` - List all instructions
- `POST /api/sender-instruction` - Add instruction
- `DELETE /api/sender-instruction/{email}` - Delete instruction

### System
- `GET /api/status` - System health
- `GET /api/history` - Action history
- `GET /api/corrections` - View corrections
- `GET /morning-pulse` - Send morning summary

---

## Common Issues

### "charmap encoding error"
- Restart server with: `set PYTHONIOENCODING=utf-8`
- Or use batch files (already configured)

### Server not responding
- Check if running: `tasklist | findstr python`
- Restart: `RESTART_SERVER.bat`

### Pending emails not showing
- Check database: `curl http://localhost:8000/api/pending`

---

## Training the Twin

### Method 1: Corrections
When revising a draft, your feedback is saved and used for future similar emails.

### Method 2: Sender Instructions
1. Go to Dashboard → Twin Brain
2. Add sender email + category + instructions
3. AI reads these when drafting replies

Example:
```
Sender: jco064690@gmail.com
Category: builder
Instructions: This is my builder. Add quotes to Builder_Tracker sheet.
```

---

## Version
Current: 2.2 (March 2026)
