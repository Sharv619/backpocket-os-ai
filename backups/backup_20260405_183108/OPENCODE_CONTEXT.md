# OpenCode Session Context - BackPocket OS

## Last Session: April 3, 2026 (Evening)

### What We Did:
- Fixed all Ruff lint issues in main.py (E701, E722, F541, F841)
- Built session/memory system - new services/session_manager.py
- Added version control tables (version_history, snapshots)
- Added interactive choices to Twin chat ([CHOICES: Option 1 | Option 2])
- Added execute-action API - records agreed actions to database
- Made Twin chat persistent - now saves to browser localStorage
- Created one-click desktop shortcuts (Twin & OpenCode)
- Added OpenCode wrapper (LAUNCH_OPENCODE.bat)
- Created Launch_BackPocket.vbs for silent startup
- Created desktop shortcut creator script
- Overhauled Submenu aesthetics (Standardized to borderless glassmorphic SVG icons).
- Fixed Flexbox layout on .chat-expanded and .instructions-section for proper scaling on resize.
- Resolved SQLITE_BUSY "database is locked" errors globally by applying 20-second queue timeouts in database.py, memory.py, and session_manager.py.
- Modernized "Edit Instruction" modal to match premium overlay styling.
- Fixed "Golden Senders" wrapping issues.
- Fixed Avatar as welcoming receptionist (fixed bottom-right, breathing animation, fades on panel open).
- Fixed Sender Rules undefined bug (rule.sender → rule.sender_email) + added Edit/Delete/Discuss/Add buttons.
- Added 3 missing section panels: Document Rules, Marketing Rules, Client Rules.
- Rewrote toggleSection() as data-driven (8 sections, cleaner code).
- Added loadCategoryInstructions() for filtered instruction views.
- Standardized ALL buttons to borderless glassmorphic styling.
- Added word-wrap/overflow-wrap for content scaling on panel resize.
- Styled client-master-table with premium hover effects.


### Key Files:
- main.py - FastAPI app with all endpoints (~1540 lines)
- services/session_manager.py - Session/memory + version control (NEW)
- services/database.py - SQLite operations
- services/gemini.py - AI operations
- static/index.html - Dashboard (~3400 lines)
- backpocket.db - SQLite database

### Decisions Made:
- Twin uses AI for all responses (no keyword matching fallback)
- Choices format: [CHOICES: Option 1 | Option 2]
- Session auto-syncs to SESSION_LOG.md
- Version control: record_version(), create_snapshot() available

### Database Tables:
- session_log - work sessions
- twin_memory - persistent context
- agreed_actions - tracked items
- version_history - like Git commits
- snapshots - like Git tags

### Pending Actions (From Twin):
- None recorded yet

### System Status:
| Component | Status |
|-----------|--------|
| Server | Running on port 8000 |
| Twin Chat | Working with memory |
| Session DB | Initialized with version control |
| Desktop Shortcuts | Created (Twin & AI) |
| Ruff | All clean |

### Common Gotchas:
1. Server needs restart after main.py changes
2. Twin memory loads on startup from database
3. Chat persists in browser localStorage
4. Session auto-syncs to SESSION_LOG.md after each session

### Version Control Functions (in session_manager.py):
- record_version(entity_type, entity_id, field, old, new)
- get_version_history(entity_type, entity_id)
- create_snapshot(name, type, data)
- get_snapshots(type)
- restore_snapshot(id)

---

*Auto-generated - updated after each session*
*This file is read automatically when OpenCode starts*