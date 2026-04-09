# BackPocket OS - Agent Documentation

## System Overview

**BackPocket OS** is an AI-powered email management system for accountants/bookkeepers. It has:
- A Digital Twin AI that helps manage emails and pending approvals
- WhatsApp integration for commands
- Google Sheets sync for client data
- Gmail integration for email management

---

## CHANGE PROTOCOL ⚡

**Before implementing ANY enhancement, update, or modification:**

### Step 1: CONTEXT (What's there now?)
- Current state of the feature/code
- How it works today
- What's already working

### Step 2: THE PROBLEM (Why change?)
- What it's lacking
- Real issue we're solving
- User pain point or gap

### Step 3: PROPOSED SOLUTION
- What the change does
- Pros (benefits)
- Cons (trade-offs, complexity)

### Step 4: ECOSYSTEM IMPACT
- Dependencies affected
- What might break
- Performance considerations
- Security implications

### Step 5: APPROVAL
- Present summary to user
- Get explicit "yes" before implementing
- If complex: also present rollback plan

### Step 6: DOCUMENT
- Update SOPs if new process
- Log decision in SESSION_LOG.md
- Add to relevant documentation

---

**Reminder phrases:**
- "Before I implement this, here's the context..."
- "Shall I proceed with this change?"
- "I've documented this in SOPs"

**SOP Categories** (use `/api/sops` endpoint):
- `system` - Server, restart, backup
- `chat` - Chat/twin features
- `email` - Email handling
- `instructions` - Twin instructions
- `debug` - Troubleshooting

---

## Open's Coding System

### Session Persistence
- **OPENCODE_CONTEXT.md** - Quick reference for current session state
- **SESSION_LOG.md** - Full history of work sessions
- **AGENTS.md** - This file - always read at session start
- **docs/ERROR_LOG.md** - Track of all errors and fixes

### Workflow at Session Start:
1. Read AGENTS.md for system overview
2. Read SESSION_LOG.md for recent sessions
3. Read OPENCODE_CONTEXT.md for quick context
4. Check for any errors in docs/ERROR_LOG.md

### Quality Tools Stack (2026 Best Practices)
- **Ruff** - Fast linter + formatter (replaces flake8, isort, black)
- **mypy** - Static type checker
- **pytest** - Testing framework
- **pre-commit hooks** - Automated checks before commits

---

## ⚠️ BEFORE EDITING FILES - ALWAYS DO THIS

**MUST DO BEFORE editing `static/index.html` or `main.py`:**

```
1. Backup first - ALWAYS, no exceptions!
2. Then read file to understand current state
3. Make changes
4. Test (python -c "import main")
```

**SOP: Fast Automated Backups**
We have a dedicated script for backing up your entire OS state before dangerous edits:
```powershell
# Create a full backup (Code, DB, Dashboard, Env)
.\scripts\backup_restore.ps1 -Action backup

# Restore a specific backup if you accidentally break the dashboard
.\scripts\backup_restore.ps1 -Action restore -TargetFolder backup_20260404_120000
```

*For quick one-off file backups:*
```powershell
copy static\index.html "static\index.html.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
```

### CRITICAL: Backup Before Dashboard Changes

**Before ANY changes to `static/index.html` or `main.py`:**

1. Create a timestamped backup: `copy static\index.html "static\index.html.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"`
2. Store backup in same folder
3. Document what changed in SESSION_LOG.md

**To restore if broken:**
```bash
# Quick restore from backup file
dir static\index.html.backup*  
copy "static\index.html.backup-YYYYMMDD-HHMMSS" static\index.html

# Or restore from git (last working version)
git checkout HEAD -- static/index.html
git checkout HEAD -- main.py
```

**Best Practice - ALWAYS do this before editing:**
```powershell
# 1. Backup dashboard
copy static\index.html "static\index.html.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

# 2. Commit current state to git
git add -A
git commit -m "Backup before [description of planned changes]"

# 3. Make changes
# ... edit code ...

# 4. Test
# ... if broken, restore with git checkout ...
```

### Skill Acquisition Workflow
1. **Research** - Search latest best practices before implementing
2. **Document** - Add findings to AGENTS.md
3. **Validate** - Run quality tools after changes
4. **Test** - Verify feature works via API/UI
5. **Review** - Check against checklist

## Key Files

### Main Application
- `main.py` - FastAPI app with all endpoints (39 KB, ~1400 lines)
  - Twin Chat: `/api/twin-chat` (line ~144)
  - Pending approvals: `/api/pending` 
  - Draft revise: `/api/revise`
  - WhatsApp webhook: `/whapi-webhook`

### Services
- `services/database.py` - SQLite operations (get_pending_approval, get_all_pending_refs, etc.)
- `services/gemini.py` - AI operations (get_gemini_client, triage_email, draft_response)
- `services/twin_brain.py` - Twin knowledge system (get_all_instructions, get_pending_approvals, etc.)
- `services/gmail.py` - Gmail API operations
- `services/whapi.py` - WhatsApp API
- `services/google_sheets.py` - Sheets sync

### Frontend
- `static/index.html` - Dashboard with Twin chat, pending emails list, draft editor

## Database

- `backpocket.db` - SQLite database
- Key tables: 
  - `pending_approvals` - Emails awaiting approval
  - `instructions` / `sender_instructions` - Twin rules
  - `action_history` - What we've done
  - `chat_conversations` - Chat threads (twin/opencode)
  - `chat_messages` - Individual messages
  - `sops` - Standard Operating Procedures
  - `twin_memory` / `agreed_actions` - Persistent memory

## Validation Commands

```bash
# Test server
python -c "import main"

# Test twin chat
curl -X POST http://localhost:8000/api/twin-chat -H "Content-Type: application/json" -d '{"message": "hello"}'

# Test database
python -c "import services.database as db; print(db.get_all_pending_refs())"

# Test Gemini
python -c "from services.gemini import test_gemini_connection; print(test_gemini_connection())"

# Lint code (after any changes)
ruff check .

# Type check (after any changes)
mypy .

# Run tests (if available)
pytest
```

## Code Review Checklist

Before any edit:
- [ ] Read the surrounding code (at least 50 lines above/below)
- [ ] Check if similar patterns exist elsewhere in the file
- [ ] Run validation commands after changes
- [ ] Test the affected endpoint

After any edit:
- [ ] Run: `python -c "import main"`
- [ ] Test the specific feature that was changed
- [ ] Check for any 500 errors

## Common Gotchas

1. **String literal issues**: When editing f-strings in main.py that contain other quotes, use triple quotes carefully
2. **Git restore**: If main.py gets corrupted, run `git checkout main.py`
3. **Server needs restart**: Changes to main.py require server restart to take effect
4. **Gemini model**: Use `gemini-2.5-flash` (not `gemini-2.0-flash` - deprecated)
5. **Windows subprocess**: Use `creationflags=subprocess.CREATE_NEW_CONSOLE` to start server in new window

## Recent Changes (2026)

- Twin chat now uses AI for all responses (not just quick replies)
- Twin has access to database (pending approvals, history, instructions)
- Chat box is resizable (CSS `resize: vertical`)
- Markdown rendering in frontend (bold, headings, bullet points)
- Fixed: Server logging issue with `use_colors=False`

## Testing Checklist

Before declaring a feature working:
- [ ] Test via curl/API directly
- [ ] Test via dashboard UI
- [ ] Check no 500 errors in logs
- [ ] Verify database state if applicable

## Code Quality Tools

### Ruff (Linter + Formatter)
```bash
# Install
pip install ruff

# Run linter
ruff check .

# Auto-fix issues
ruff check . --fix

# Format code
ruff format .
```

### mypy (Type Checker)
```bash
# Install
pip install mypy

# Run type check
mypy .
```

### pytest (Testing)
```bash
# Install
pip install pytest

# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=term-missing
```

## Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run all hooks manually
pre-commit run --all-files
```

## Skill Research Notes

### Code Review Best Practices (2026)
- Pull request review is the last checkpoint before code enters main branch
- Every bug/security vulnerability that survives review has direct path to production
- Code review should be reframed as mentorship and knowledge sharing opportunity
- Senior engineers focus on: architecture, edge cases, security, performance

### Python Testing Best Practices
- Use pytest fixtures for setup/teardown
- Mock external dependencies
- Aim for 80%+ code coverage
- Run tests in CI/CD pipeline

### Python Code Quality Stack (2026)
- **Ruff** - Fastest linter (10-100x faster than alternatives)
- **mypy** - Static type checking
- Together they cover linting, formatting, and type checking

### Microsoft Agent Lightning (Future Enhancement)
- GitHub: microsoft/agent-lightning (16.5k stars)
- Train/optimize AI agents with Reinforcement Learning
- Works with any agent framework (LangChain, AutoGen, CrewAI, etc.)
- Could optimize Twin AI's email triage decisions over time
- Currently NOT implemented - future enhancement after system is stable

## Baseline Code Status

### Ruff Issues (1521 total)
Top issues to address:
- E701: Multiple statements on one line (31)
- E402: Module import not at top (20)
- F541: f-string without placeholders (11)
- F401: Unused imports (30+)
- E722: Bare except (8)

### mypy Issues (4 errors)
- Stub packages needed: `types-requests`
- Module name conflicts: `services/gmail.py`

## Baseline Code Status (April 2, 2026)

### Ruff - All Issues Fixed ✅
- E701: Fixed 15 multi-statement lines
- E402: Added noqa comments for intentional deferred imports
- F541: Fixed 2 f-strings without placeholders
- E722: Fixed 4 bare except clauses
- F841: Fixed 2 unused variables

### Session & Memory System

**New Files:**
- `services/session_manager.py` - Session logging, Twin memory, agreed actions

**Features:**
- Twin remembers past sessions and pending actions
- Interactive choices in chat: `[CHOICES: Option 1 | Option 2]`
- Execute agreed actions: `/api/execute-action`
- Session auto-sync to SESSION_LOG.md

**API Endpoints:**
- `/api/twin-chat` - Chat with Twin (now includes memory context)
- `/api/execute-action` - Log sessions, record agreed actions

## Action Items

- [x] Fix unused imports in main.py
- [x] Fix E701 multi-statement lines
- [x] Fix E402 import order (with noqa)
- [x] Fix E722 bare except
- [x] Fix F541 f-strings
- [x] Add session persistence system
- [x] Add interactive choices to Twin
- [x] Add execution capability

## Common Gotchas

1. **Restart server** after main.py changes
2. **Twin memory** loads automatically on startup
3. **Session log** can be viewed in SESSION_LOG.md
- [ ] Install type stubs for mypy
- [ ] Resolve gmail module conflict
