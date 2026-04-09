# 🍒 BackPocket Twin: Transition to OpenCode
### From: Antigravity (VS Code) → To: OpenCode (Terminal AI)
**Date:** March 2026 | **Written for:** Cherry (5-year-old proof! 👧)

---

> IMPORTANT: You are NOT losing Antigravity. Think of this like adding a second coding helper
> that sits inside your terminal. Antigravity stays available in VS Code. OpenCode gives you a
> BIGGER free bucket of tokens so you can keep building without running out.

---

## What is OpenCode? (Simple Version)

Imagine you have a very smart helper who lives inside your black command window (the terminal).
You type normal English to it, point it at your code files, and it reads, fixes, and writes
code — just like Antigravity does, but:

| Feature | Antigravity (VS Code) | OpenCode (Terminal) |
|---|---|---|
| Where it lives | Inside VS Code | Inside your Terminal |
| Cost | Uses Gemini credits (limited) | Bring your own API key — use Gemini FREE tier OR Ollama (free!) |
| Privacy | Cloud-based | Runs locally with Ollama — nothing leaves your PC |
| Token limits | Platform quota | Only limited by the AI model you choose |
| Code awareness | Reads open files | Reads your entire project folder |
| Best for | Quick edits, chat | Deep dives, building whole features |

Bottom line: OpenCode connected to your Mini-PC's Ollama = 100% free, 100% private, unlimited tokens.

---

## BEFORE YOU START — Checklist

Make sure you have these ready:
- [ ] Your BackPocket_MVP folder on Desktop (you already have this)
- [ ] Node.js installed (we will check below)
- [ ] Your Gemini API key (in your .env file as GEMINI_API_KEY)
- [ ] Ollama running on your Mini-PC (already set up)

---

## PART 1: Install OpenCode on Your DESKTOP PC

### Step 1 — Check if Node.js is installed
Open PowerShell (search "PowerShell" in Start Menu, right-click → Run as Administrator) and type:

    node --version

- If you see something like v20.x.x → Node.js is ready! Skip to Step 2.
- If you see an error → Go to https://nodejs.org, click the big green "LTS" button,
  download and install it. Then restart PowerShell.

### Step 2 — Install OpenCode (one command!)
In the same PowerShell AS ADMINISTRATOR, type:

    npm install -g opencode-ai

Wait for it to finish (takes 1-2 minutes). You will see lots of green text — that is good!

### Step 3 — Verify it worked

    opencode --version

You should see a version number. If you do — OpenCode is installed!

---

## PART 2: First-Time Setup — Connect Your AI Brain

OpenCode needs to know which AI to use. You have TWO options:

### Option A: Use Gemini (cheapest cloud option — same as Antigravity)
Run: opencode
When it opens, type: /config and set your provider to Google Gemini.
Enter your GEMINI_API_KEY from your .env file.

### Option B: Use Ollama on Mini-PC (FREE, PRIVATE, UNLIMITED — RECOMMENDED)
Run: opencode
When it opens, type: /config and set your provider to Ollama.
Set the base URL to: http://<YOUR-MINI-PC-IP>:11434
Set the model to: deepseek-r1:1.5b

TIP: Option B is best for privacy. Your code never leaves your home network.
This is the "self-sufficient small business" choice.

---

## PART 3: Start Working on Your BackPocket Twin

### Step 1 — Open a Terminal in your project folder
1. Open VS Code
2. Open the terminal inside VS Code (Ctrl + backtick)
3. Make sure you are in your project: cd c:\Users\Cherry\BackPocket_MVP

### Step 2 — Launch OpenCode inside your project

    opencode

A beautiful interactive screen will open. This is your new coding buddy!

### Step 3 — Paste the "Brain Paste" (copy this entire block into OpenCode on first use)

I am Cherry, owner of BackPocket System.io. I am building an AI Digital Twin called
"BackPocket Twin" that triages my emails, drafts replies, and sends me WhatsApp notifications
for approval before anything is sent.

My project is in the current folder. Please read the following files to understand the full
context before we start:
- docs/SOP.md (the rules and tier system)
- docs/JOURNEY.md (what we have built so far and lessons learned)
- docs/OPENCODE_TRANSITION.md (this handover document)
- main.py (the main FastAPI server)
- services/gmail.py (email fetching, archiving, rescue)
- services/gemini.py (AI triage and draft logic)
- services/whapi.py (WhatsApp notifications)

KEY RULES — never break these:
1. Privacy first: Use Ollama locally whenever possible, never send client data to external APIs unnecessarily.
2. The Twin NEVER sends emails without my WhatsApp approval. Every email gets a Ref# and waits for "approve <ref>".
3. Tier 1 (Clients) and Tier 2 (Govt/Assoc) emails ALWAYS stay in inbox — never archive them.
4. Tier 3 (Suppliers) and Tier 4 (Portal digests) get archived after logging.
5. Tier 5 (Spam) goes to Trash.
6. The SQLite database (services/database.py) stores all pending approvals — not in memory.
7. token.json = main Gmail account. token_imap_*.json = Outlook/other accounts.

Once you have understood all of this, tell me you are ready and ask what I want to build next.

---

## PART 4: Install OpenCode on Your MINI-PC

Repeat the same steps on your Mini-PC so you can also code there:

1. Open Terminal on Mini-PC
2. Run: npm install -g opencode-ai
3. Run: opencode --version (verify it worked)
4. When starting: use Ollama as the provider (it is already running locally there!)
5. Navigate to your project: cd /path/to/BackPocket_MVP

---

## How to Switch Between Antigravity and OpenCode

| When to use Antigravity | When to use OpenCode |
|---|---|
| Quick file edits in VS Code | Building whole new features |
| Antigravity still has credits | Antigravity tokens are exhausted |
| You want the VS Code chat sidebar | You want full project-wide AI reads |
| Debugging with file previews | Complex logic changes across multiple files |

You can use BOTH on the same day! They both read the same project folder.

---

## If OpenCode Gets Confused — Quick Reset Prompt

Copy and paste this if OpenCode gives wrong answers:

    Stop. Refresh your context. Re-read docs/SOP.md and docs/JOURNEY.md.
    Remember: You are helping Cherry build a privacy-first AI Twin for her small business.
    The golden rule: NO email is ever sent without WhatsApp approval from Cherry.
    Now tell me what you currently understand about the project state.

---

## The "Best of Both Worlds" Strategy

    ANTIGRAVITY (VS Code)
       Quick fixes, file edits, chat sidebar
       Use when credits are available
                    +
    OPENCODE (Terminal)
       Big feature builds, deep code reads
       Powered by Ollama = FREE + PRIVATE
                    +
    OLLAMA (Mini-PC)
       The free brain that powers OpenCode
       deepseek-r1:1.5b model always running
       Zero cost, zero cloud, zero privacy risk

---

## Quick Reference Card — Print This!

| Task | Command |
|---|---|
| Start OpenCode | opencode |
| Show settings | /config |
| Read a specific file | /file services/gmail.py |
| Run a terminal command | /run python main.py |
| Start new session | /new |
| List saved sessions | /sessions |
| Exit OpenCode | /quit or Ctrl+C |

---

## What Antigravity Knows That OpenCode Needs to Learn

OpenCode starts fresh each session. Always paste the Brain Paste (Part 3, Step 3) at the
start of EVERY new session. It will read your docs and be ready in seconds.

Key things to always remind OpenCode:
1. WhatsApp approval is MANDATORY — the twin never auto-sends
2. Tier 1 + Tier 2 emails NEVER get archived — they stay in inbox
3. Ollama is the free fallback — use it for cost savings
4. SQLite database stores pending approvals (not in-memory)
5. token.json = main Gmail account, token_imap_*.json = Outlook accounts
6. The dashboard is at http://localhost:8000/dashboard
7. The .env file has all API keys (GEMINI_API_KEY, WHAPI_TOKEN, FOUNDER_PHONE etc)

---

"Building a Digital Twin is not a sprint — it is a marathon. Every tool switch is just a pit stop." Cherry 2026
