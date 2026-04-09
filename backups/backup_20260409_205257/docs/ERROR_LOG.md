# 🩺 BackPocket Twin: Error Log & Doctor's Notes 🩹

This log tracks every time the Twin "sneezed" or "tripped," and how we fixed it. This is how we ensure the same mistake never happens twice.

---

## 🗓️ March 27, 2026: LSP Type Checking Issues

**The Problem:** The LSP (Language Server Protocol) found type errors across 4 files.

**Files Affected:**
| File | Errors | Type |
|------|--------|------|
| `main.py` | 5 | Await/None issues |
| `services/gemini.py` | 10 | None/strip issues |
| `services/whapi.py` | 4 | None assignment |
| `services/imap.py` | 6 | Decode/type issues |

**Status:** ⚠️ NOT CRITICAL — These are strict type-checking warnings, not runtime errors.

**The Impact:** 
- Likely not breaking runtime but could mask real bugs
- Common in Python code that was written quickly
- Easy to fix with proper null checking

**Recommended Fix:**
```python
# Before (problematic)
text = response.strip()

# After (safe)
text = (response or "").strip()
```

**Status:** 📋 PENDING — To be fixed in next sprint

---

## 🗓️ March 11, 2026: The "OAuth Ghost" 👻
- **The Problem**: The system kept asking to "Log in" to Google even though we already did.
- **The Cause**: We were using a "Service Account" for Sheets but an "OAuth App" for Gmail. They weren't talking to each other properly.
- **The Cure**: We linked them both using the `credentials.json` hub. Now they are best friends.

---

## 🗓️ March 12, 2026: The "Port 8000 War" ⚔️
- **The Problem**: The Twin refused to start, saying "Port 8000 is already taken!"
- **The Cause**: An "old version" of the Twin was still running in the background. We had a "Ghost Engine"!
- **The Cure**: We wrote a script to find and "Kill" the ghost process. Now the engine starts fresh every time.

---

## 🗓️ March 13, 2026: The "Big Boss" Leak 🎭
- **The Problem**: Emails from `yourwebaccountant.com` were replying with `bigbossgroup.com.au`.
- **The Cause**: The system was looking at the wrong part of the email header ("Delivered-To" instead of "To"). It got confused about which hat to wear.
- **The Cure**: We taught the Twin to look at the **Original To** address. Now it wears the correct brand hat 100% of the time.

---

## 🗓️ March 15, 2026: The "Silent Burial" (Rowan Rule) 🧘
- **The Problem**: A client email (Rowan) was archived in `Updates_Archive` without any notification.
- **The Cause**: The AI correctly triaged it as "Tier 4 (Update)" based on the snippet, but because it didn't recognize him as a client at that step, it filed it silently.
- **The Cure**: I moved the "Check Master List" step to the very top. Now, if the Twin sees a client, it NEVER files it silently, even if it's just a "Thank you" note.

---

## 🗓️ March 15, 2026: The "Indentation Trap" 🪤
- **The Problem**: The "Approve" command was being ignored.
- **The Cause**: A developer mistake (misalignment) caused the webhook logic to skip the command processing block entirely.
- **The Cure**: Re-aligned the code blocks. I also added a "Command Audit" to the logs so we can see exactly what the Twin "hears" from WhatsApp.

---

## 🗓️ March 15, 2026: The "Ngrok Auth Token" Trap
- **The Problem**: Ngrok refused to connect (ERR_NGROK_4018).
- **The Cause**: Auth token was outdated or missing from config.
- **The Cure**: Updated ngrok authtoken via `ngrok config add-authtoken <token>`

---

## 🗓️ March 17, 2026: The "Baseline Limit" Wall
- **The Problem**: Gemini API hitting rate limits during batch processing.
- **The Cause**: Too many emails being sent individually instead of batched.
- **The Cure**: Implemented Tri-Layer Triage Strategy with batching and Ollama fallback.

---

## 🗓️ March 27, 2026: File Organization Cleanup

**The Problem:** Files scattered across root level — backups, dumps, redundant scripts mixed with core code.

**Files Removed:**
- `services/whapi.py.bak` — Old backup
- `services/whapi.py.backup` — Another old backup  
- `OLLAMA_CODE_DUMP.txt` — Debug dump, no longer needed
- `out.txt` — Debug output, no longer needed
- `new_whapi_code.txt` — Redundant, code already in whapi.py

**Files Organized:**
- Old scripts moved to `scripts/` if useful
- Logs consolidated to `logs/` directory
- Credentials remain in root (can't move .env)

**Status:** ✅ COMPLETE

---

## 🗓️ March 27, 2026: OpenRouter Integration

**The Setup:**
- Added OpenRouter API key to .env
- Verified 75+ models available
- Tested Claude via OpenRouter ✅
- Created .opencode_config.json for optimal setup

**Models Connected:**
| Task | Model | Status |
|------|-------|--------|
| Coding | Claude 3.5 Sonnet | ✅ Ready |
| Communication Coach | GPT-4o | ✅ Ready |
| Email Triage | Gemini | ✅ Already working |
| Fallback | Ollama | ✅ Already working |

**Status:** ✅ COMPLETE

---

## 📊 Error Categories Summary

| Category | Count | Status |
|----------|-------|--------|
| Authentication/OAuth | 2 | ✅ Fixed |
| Port/Process Issues | 2 | ✅ Fixed |
| Logic/Matching | 3 | ✅ Fixed |
| API Rate Limits | 1 | ✅ Fixed (Tri-Layer) |
| Type Checking | 4 files | ⚠️ Pending |
| File Organization | 1 | ✅ Complete |

---

## 🛠️ How to use this log:

1. **Check here first** if something feels "broken."
2. If you find a new bug, tell the AI: *"Log this error in the doctor's notes."*
3. Include: Date, Problem, Cause, Cure, Status

---

## ✅ Auto-Update Process

When the AI (OpenCode) fixes an issue, it automatically:
1. Updates this error log with the fix
2. Adds it to JOURNEY.md as a "War Story"
3. Updates SYSTEM_INVENTORY_MASTER.md if hardware/software changed
4. Updates SYSTEM_CONTEXT.md if architecture changed

**This ensures the documentation is always current.**

---

*Last Updated: 2026-03-27*
*Building in public. Every error is a lesson learned.*
