# SYSTEM CONTEXT: BackPocket OS (The Smarter Twin)
**Last Updated:** 2026-03-31
**Version:** 3.1

---

## RECENT CHANGES (Session Log)

### 2026-03-31 - Cloudflare Tunnel + Unified Instructions System
- ✅ Installed cloudflared CLI on desktop
- ✅ Created Cloudflare tunnel "backpocket-os" 
- ✅ Configured DNS: backpocket-os.backpocketsystem.io → localhost:8000
- ✅ Tunnel running and accessible at https://backpocket-os.backpocketsystem.io/dashboard
- ✅ Updated database schema (instructions table with new fields)
- ✅ Added instruction categories (14 default categories)
- ✅ Added revision history tracking
- ✅ Updated API endpoints: GET/POST/PUT/DELETE /api/instructions
- ✅ Updated dashboard with dynamic category dropdown, critical toggle, test mode toggle
- ✅ Created START_TUNNEL.bat for easy tunnel startup
- ✅ **POPULATED DATABASE with 14 operational instructions:**
  - ✅ Human-in-the-loop: NEVER auto-send, always draft first
  - ✅ WhatsApp approval workflow (approve, revise commands)
  - ✅ 5-tier email triage system
  - ✅ Document extraction rules (ABN, Invoice data, etc.)
  - ✅ 5 Agent capabilities (Accountant, Auditor, Admin, Coach, Marketing)
  - ✅ Google Sheets sync for instructions backup
  - ✅ Sender-specific instructions (stored in sender_instructions table)
- ✅ Found existing sender instructions in database:
  - cherry@yourwebaccountant.com → Portal updates (SuiteDash)
  - jco064690@gmail.com → Builder tracker + quote comparison

### 2026-03-30 - Agent Chat + Document Processing Added
- ✅ Added `/api/agent-chat` endpoint with 5 AI agents (Accountant, Auditor, Admin, Coach, Marketing)
- ✅ Created `services/document_processor.py` - handles PDF, DOCX, XLSX, TXT, images
- ✅ Added document endpoints: `/api/documents`, `/api/document/process`, `/api/document/rename`, `/api/document/upload`
- ✅ Updated dashboard (`static/index.html`) with premium dark theme, Agents tab, Docs tab, Coach tab
- ✅ Added document processing packages: pymupdf, python-docx, openpyxl, Pillow, watchdog, aiofiles, python-multipart
- ✅ Enhanced Twin Chat with full system knowledge (email triage, WhatsApp commands, agents, docs)
- ✅ Research: MCP servers for Xero/MYOB/QuickBooks integration
- ✅ Research: Visual workflow tools (n8n, LangFlow)

### 2026-03-27 - Twin v2.2 Launch
- ✅ Email triage with 5 tiers
- ✅ WhatsApp approvals via Whapi
- ✅ Google Sheets logging
- ✅ Gemini AI for drafting

---

## 🔬 RESEARCH: Agent Tools & Skills (MCP)

### What is MCP (Model Context Protocol)?
MCP servers give AI agents REAL functions/tools they can call. Instead of just "thinking" about Xero, the agent can actually query Xero.

### MCP Servers Available:

| MCP Server | What It Does |
|------------|--------------|
| **Xero MCP** | Query invoices, cash flow, P&L, outstanding payments |
| **QuickBooks MCP** | Same as Xero for QB |
| **MYOB** | Australian accounting software |
| **Google Drive/Sheets** | Read/write files, update spreadsheets |
| **Slack/Discord** | Send messages |
| **GitHub** | Code management |

### How to Implement:
1. Install MCP server: `npx @modelcontextprotocol/server-xero`
2. Connect to AI agent
3. Agent can now query: "Get all unpaid invoices" → Xero API → Real data

### Research Sources:
- https://playbooks.com/mcp/xero-accounting
- https://developer.xero.com/ai
- https://www.agentx.so/mcp/xero

---

## 📄 RESEARCH: Document Processing Tools

| Tool | What It Does | Cost |
|------|--------------|------|
| **LlamaParse** | Advanced PDF OCR + extraction | Free tier |
| **Unstract** | End-to-end document pipeline | Self-hosted |
| **Veryfi** | Real-time OCR API | Paid |
| **PyMuPDF** | Basic PDF text extraction | Free |

### Current Implementation:
- PyMuPDF for basic PDF text
- python-docx for Word files
- openpyxl for Excel
- Pillow for images

### Next Steps:
- Add LlamaParse for advanced OCR
- Create document routing (→ Xero, → Client folder, → Audit queue)

---

## 🔀 RESEARCH: Visual Workflow Tools

| Tool | Best For | Cost |
|------|----------|------|
| **n8n** | Self-hosted automation | Free |
| **Make (Integromat)** | Visual workflows | Free tier |
| **LangFlow** | AI workflow builder | Free |
| **ComfyUI** | Visual AI workflows | Free |

### Recommendation:
Build custom visual workflow in dashboard using **interactive node graph**:
- Each node = Agent or action
- Connectors show data flow
- Click node to edit/instruct
- Drag-drop to rewire

---

## 1. MISSION (For Cherry)

We are building a **super smart robot assistant** - a true "One-Man Army" system - for your accounting firm that:

- Works **24/7** without getting tired
- Keeps everything **private** (your data stays on your computers)
- Costs **$0** to run (uses free local AI)
- Handles **EVERYTHING** in your business, not just emails
- **NEVER does anything** without asking you first (Human-in-the-Loop)

**The Goal:** Automate 100% of your business operations with zero human headcount.

---

## 2. THE SMARTER TWIN FEATURE SET (The Modules)

### 📨 EMAIL MODULE
| Feature | What It Does |
|---------|--------------|
| 24/7 Triage | Checks emails 24/7, sorts into 5 tiers |
| Client Matching | Matches senders to your Client Master sheet |
| Draft Replies | Writes professional replies that sound like you |
| WhatsApp Approvals | Sends you a message on WhatsApp to approve before sending |
| Deduplication | Prevents same email from being processed twice |

### 📄 DOCUMENTS MODULE
| Feature | What It Does |
|---------|--------------|
| OCR Scanning | Reads text from scanned PDFs and images |
| Classification | Sorts documents (invoices, contracts, receipts) |
| Field Extraction | Pulls out important info (dates, amounts, names) |
| Encode Queue | Tracks documents waiting to be processed |

### 💰 ACCOUNTING MODULE
| Feature | What It Does |
|---------|--------------|
| QBO/Xero/MYOB API | Posts invoices and payments to accounting software |
| Human-in-the-Loop | Never posts anything without asking you first |
| Reconciliation | Matches bank transactions to entries |

### 👥 CRM/PORTAL MODULE
| Feature | What It Does |
|---------|--------------|
| SuiteDash Integration | Manages projects and proposals |
| E-Sign Tracking | Tracks signed documents |
| Client Portal | Clients can access their documents |

### 🤖 SCREEN AGENT (RPA)
| Feature | What It Does |
|---------|--------------|
| Power Automate Desktop | Controls desktop apps automatically |
| ATO Portal Automation | Logs into government portals for you |
| Access Elite | Works with legacy database apps |

### 📢 MARKETING MODULE
| Feature | What It Does |
|---------|--------------|
| AI Content Generation | Creates social media posts and newsletters |
| Inclusive Language | Uses warm, accessible, culturally aware words |
| Scheduling | Posts at the best times automatically |

### 🛡️ GOVERNANCE MODULE
| Feature | What It Does |
|---------|--------------|
| Audit Logs | Tracks everything the system does |
| Risk Flagging | Warns you about unusual activity |
| Compliance Checks | Makes sure you're following rules |

### 🎤 COMMUNICATION COACH (New!)
| Feature | What It Does |
|---------|--------------|
| Draft Review | Reviews every email draft before you see it |
| Authority Check | Makes sure you sound confident, not wishy-washy |
| Clarity Check | Ensures the call-to-action is clear |
| Empathy Check | Confirms warm, inclusive tone |
| Power Version | Offers a stronger version if needed |
| Confidence Score | Rates how confident your communication sounds |
| Voice Practice | **Voice mode** so you can practice speaking confidently |

---

## 3. THE TWO-BRAIN SYSTEM

| Brain | Computer | What It Does | Stays On? |
|-------|----------|--------------|-----------|
| **BRAIN 1** | Mini-PC (BPS-Brain-01) | Always-on指挥中心. Runs workflows, checks emails, sends WhatsApp. | 24/7 |
| **BRAIN 2** | Windows Desktop (BB-Desktop) | Heavy thinker. Does AI work, OCR scanning, voice practice. | When needed |
| **MEMORY** | Synology NAS | Filing cabinet. Stores documents long-term. | Always on |
| **NOTEBOOK** | Google Sheets | Quick notes. Client list, activity log. | Always on |

---

## 4. THE FIVE-TIER EMAIL SORTING SYSTEM

| Tier | Name | What It Means | Action |
|------|------|---------------|--------|
| 1 | **Clients** | Real customers who pay you | Stay in inbox + WhatsApp you + **Draft reply** |
| 2 | **Government** | ATO, banks, lawyers, ASIC | Stay in inbox + WhatsApp you + **NO draft reply** |
| 3 | **Suppliers** | People you buy from | Archive + Log to Google Sheets |
| 4 | **Portals** | Auto-emails, newsletters | Archive + Log to Google Sheets |
| 5 | **Spam** | Junk, scams, nonsense | Delete forever |

**Attachment Rule:** Save attachments to relevant folder + log to Google Sheets

---

## 5. THE TRI-LAYER TRIAGE STRATEGY (How We Decide)

Think of it like getting help with homework:

| Layer | Name | When It Acts | Cost |
|-------|------|--------------|------|
| **Layer 0** | Rules (Free) | First check | $0 - Uses simple if-then rules |
| **Layer 1** | Batch AI (Gemini) | If rules need help | Cheap - Batches emails to save money |
| **Layer 2** | Local AI (Ollama) | If nothing else works | $0 - Runs on your own computer |

**Golden Rule:** Always try the free option first!

---

## 6. THE COMMUNICATION COACH EXPLAINED

### How It Works:

```
AI writes draft → Coach reviews → You see improved version + score → You approve
```

### What The Coach Checks:

| Check | Bad Example | Good Example |
|-------|-------------|--------------|
| **Authority** | "I think maybe we could..." | "Based on our analysis..." |
| **Clarity** | "Can we possibly look at this sometime?" | "Please review and confirm by Friday." |
| **Empathy** | "I'm sorry but I have to tell you..." | "I understand this is important, and here's..." |

### The Confidence Score:
- **90-100:** Strong, confident, professional
- **70-89:** Good, minor tweaks needed
- **50-69:** Needs work, Coach offers "Power Version"
- **Below 50:** Rewrite recommended

### Voice Practice Mode:
- You can **speak** your responses
- The Coach **listens** and gives feedback
- Practices Australian and American accents
- Helps you sound confident and clear

---

## 7. CODING PHILOSOPHY (Our Robot Rules)

| Rule | Meaning | Why It Matters |
|------|---------|-----------------|
| **NO SUBSCRIPTIONS** | Prefer free, self-hosted solutions | You don't want to pay monthly fees forever |
| **CONFIG-DRIVEN** | Settings in Sheets/JSON, not hard-coded | So others can use the robot too |
| **HUMAN-IN-THE-LOOP** | Always draft and ask for approval | You stay in control, never auto-send |
| **INCLUSIVE DESIGN** | Use kind, clear, accessible language | Works for everyone, everywhere |
| **PRODUCT-READY** | Every code must be modular and reusable | Can sell to other firms later |

---

## 8. DIRECTORY STRUCTURE (The BackPocket OS)

```
BackPocket_OS/
├── main.py                     # Main application (FastAPI server)
├── requirements.txt            # Python packages needed
├── .env                        # Secrets (API keys, passwords)
│
├── services/                   # All the robot's abilities (THE MODULES)
│   ├── email/                  # EMAIL MODULE
│   │   ├── triage.py          # Sorts emails into 5 tiers
│   │   ├── gmail.py           # Gmail connection
│   │   ├── imap.py            # Outlook connection
│   │   ├── dedup.py           # Prevents duplicate processing
│   │   └── client_match.py    # Matches senders to Client Master
│   │
│   ├── documents/             # DOCUMENTS MODULE
│   │   ├── ocr.py             # Reads text from images/PDFs
│   │   ├── classifier.py      # Sorts documents by type
│   │   ├── extractor.py        # Pulls out important fields
│   │   └── encode_queue.py    # Tracks pending documents
│   │
│   ├── accounting/            # ACCOUNTING MODULE
│   │   ├── qbo.py             # QuickBooks Online connection
│   │   ├── xero.py            # Xero connection
│   │   ├── myob.py            # MYOB connection
│   │   └── reconciliation.py   # Matches bank transactions
│   │
│   ├── crm/                   # CRM/PORTAL MODULE
│   │   ├── suitedash.py       # SuiteDash integration
│   │   ├── esign.py           # E-signature tracking
│   │   └── client_portal.py   # Client access portal
│   │
│   ├── rpa/                   # SCREEN AGENT (RPA) MODULE
│   │   ├── power_automate.py  # Power Automate Desktop control
│   │   ├── ato_portal.py      # ATO portal automation
│   │   └── elite_access.py    # Access Elite automation
│   │
│   ├── marketing/             # MARKETING MODULE
│   │   ├── content_gen.py     # AI content generation
│   │   ├── scheduler.py       # Post scheduling
│   │   └── social_ai.py        # Social media AI
│   │
│   ├── governance/            # GOVERNANCE MODULE
│   │   ├── audit_log.py       # Tracks all actions
│   │   ├── risk_flags.py      # Warns about unusual activity
│   │   └── compliance.py      # Compliance checks
│   │
│   ├── coach/                 # COMMUNICATION COACH MODULE (NEW!)
│   │   ├── review.py          # Reviews email drafts
│   │   ├── authority_check.py # Checks for weak language
│   │   ├── clarity_check.py   # Checks call-to-action
│   │   ├── empathy_check.py   # Checks tone
│   │   ├── power_version.py   # Generates stronger version
│   │   ├── confidence_score.py # Rates the draft
│   │   └── voice_practice.py  # Voice practice mode (TTS/STT)
│   │
│   ├── ai/                    # AI CORE (SHARED)
│   │   ├── gemini.py          # Google Gemini (Layer 1)
│   │   ├── ollama.py          # Local Ollama (Layer 2)
│   │   └── triage_brain.py    # The triage decision logic
│   │
│   ├── communication/          # COMMUNICATION (SHARED)
│   │   ├── whapi.py           # WhatsApp connection
│   │   ├── approval_flow.py   # Approval workflow
│   │   └── notifications.py    # Alert system
│   │
│   ├── storage/               # STORAGE (SHARED)
│   │   ├── database.py        # SQLite database
│   │   ├── sheets.py          # Google Sheets connection
│   │   └── nas.py            # Synology NAS connection
│   │
│   ├── diagnostics.py         # Health checks
│   ├── self_check.py          # Self-nudging (reminds of old items)
│   └── local_audit.py         # Self-audit using Ollama
│
├── config/                     # Configuration (NOT hard-coded!)
│   ├── tiers.json            # Email tier rules
│   ├── templates/             # Email draft templates
│   ├── documents/             # Document classification rules
│   ├── accounting/           # Accounting mapping rules
│   ├── coach/                # Communication style rules
│   └── settings.json         # System settings
│
├── static/                     # Web dashboard files
│   ├── index.html
│   ├── app.js
│   └── style.css
│
├── docs/                       # Documentation for humans
│   ├── SOP.md                # User manual
│   ├── JOURNEY.md            # Development notes
│   ├── CHERRY_STYLE.txt      # How Cherry talks (for AI)
│   └── TWIN_DIAGNOSIS_SOP.md # Troubleshooting guide
│
├── scripts/                    # Helper scripts
├── data/                       # Local storage (NAS-synced)
└── logs/                       # Audit trails and errors
```

---

## 9. HOW CHANGES AFFECT PRODUCTIZATION

### What Is Productization?
Making BackPocket OS into a **product others can buy and use**. Think of it like turning your personal recipe into a cookbook others can follow.

### What Makes Something PRODUCTIZABLE?

**✅ YES - Makes It Sellable:**
- Config-driven (rules in Sheets/JSON, not hard-coded)
- Works for ANY small business, not just you
- Still works if cloud AI (Gemini) is down (Ollama fallback)
- User always stays in control (approval required)
- Clear documentation that explains "why"
- Self-healing (recovers from errors automatically)
- Modular (can be installed piece by piece)

**❌ NO - Kills Productization:**
- Hard-coded client names, emails, personal details
- Assumes only one user/business
- No fallback when external services fail
- Auto-sends without approval
- Removes documentation
- Breaks the Tri-Layer Triage Strategy
- Only works on Cherry's specific setup

### Before Any Change, Ask:
1. Would this work for ANY small business owner?
2. Is this configurable (in Sheets/.env/config) or hard-coded?
3. Does it still work if Gemini is down? (Layer 2 fallback)
4. Is the user still in control? (Human-in-the-Loop preserved?)
5. Can I explain "why" this change exists?
6. Can someone install just this piece? (Modular?)

---

## 10. HOW I WORK WITH YOU (My Process)

When you ask me to do something, I will:

**Step 1: Read the Context**
- Read `SYSTEM_CONTEXT.md` (this file)
- Find relevant files in the codebase
- Understand the current logic

**Step 2: Explain in Plain English**
- "Cherry, this part of the robot does X by Y"
- Use simple words, no jargon
- Explain WHY we're doing this, not just HOW

**Step 3: Show You the Code**
- Clean, well-commented implementation
- Follow existing patterns in the codebase
- Make it productizable (see Section 9)

**Step 4: Tell You the Impact**
- "This change helps/hurts productization because..."
- Which module does it affect?
- Any risks or edge cases?

**Step 5: Self-Test**
- Run diagnostics before changes
- Run diagnostics after changes
- Make sure nothing breaks

**Step 6: Wait for Your Approval**
- "Cherry, do you want me to do this?"
- Don't change anything until you say YES

---

## 11. SELF-TESTING & SELF-DIAGNOSIS

### Quick Health Check
```bash
# 1. Check if the server is running
python -c "import requests; print(requests.get('http://localhost:8000/health').json())"

# 2. Run diagnostics
python scripts/run_diagnostics.py

# 3. Check logs for errors
python scripts/tail_logs.py --errors
```

### Module-Specific Tests
```bash
# Test EMAIL module
python -c "from services.email.triage import run_triage; run_triage()"

# Test DOCUMENTS module
python -c "from services.documents.ocr import scan_document; scan_document('test.pdf')"

# Test AI module
python -c "from services.ai.gemini import test_connection; test_connection()"

# Test COMMUNICATION COACH
python -c "from services.coach.review import review_draft; review_draft('Hi, I think maybe...')"
```

### Daily Checklist
- [ ] Server running without errors
- [ ] WhatsApp messages coming through
- [ ] Google Sheets updating
- [ ] No failed messages in `logs/failed_whatsapp_queue.json`
- [ ] Ollama responding (if used)
- [ ] All modules healthy (run full diagnostics)

---

## 12. IMPORTANT COMMANDS

```bash
# Start the Twin
uvicorn main:app --reload --port 8000

# Install dependencies
pip install -r requirements.txt

# Run all diagnostics
python -c "from services.diagnostics import run_all; run_all()"

# Open dashboard
# http://localhost:8000
```

---

## 13. WHATSAPP COMMANDS (How You Talk to Your Twin)

| You Say | Twin Does |
|---------|-----------|
| `approve <ref>` | Sends the draft email |
| `revise <ref>: feedback` | Rewrites the draft based on your feedback |
| `add <ref>` | Adds sender to whitelist (Tier 1) |
| `supplier <ref>` | Marks sender as supplier (Tier 3) |
| `spam <ref>` | Deletes email forever |
| `archive <ref>` | Archives email |
| `find <query>` | Searches your emails |
| `pending` | Shows all emails waiting for approval |
| `self-check` | Runs system diagnostics |
| `coach review` | Reviews your last draft with Coach |
| `voice practice` | Starts voice practice mode |

---

## 14. THE BACKPOCKET OS ROADMAP

### Phase 1: Foundation ✅ COMPLETE
- [x] Email triage with 5 tiers
- [x] WhatsApp approvals
- [x] Google Sheets logging
- [x] Tri-Layer AI fallback
- [x] Dashboard with dark theme

### Phase 2: Documents ✅ COMPLETE
- [x] PDF, DOCX, XLSX, TXT, image processing
- [x] Text extraction via PyMuPDF
- [x] Key data extraction (emails, phones, ABN, amounts, invoice numbers)
- [x] Auto-generate meaningful filenames
- [x] File upload API

### Phase 3: Accounting ⚠️ IN PROGRESS
- [x] Agent chat endpoint with Accountant persona
- [ ] QBO/Xero/MYOB API integration
- [ ] Human-in-the-loop posting
- [ ] Reconciliation

### Phase 4: Agents ✅ COMPLETE (5 agents now!)
- [x] 5 AI Agents: Senior Accountant, Senior Auditor, Admin Assistant, Communication Coach, Marketing
- [x] Agent chat API endpoint
- [x] Dashboard Agent tab with chat modal
- ⚠️ Phase 4.1: Add MCP tools (Xero, MYOB, QuickBooks)
- ⚠️ Phase 4.2: Agents can work together (orchestration)
- [ ] Persistent memory (Letta) - NOT YET IMPLEMENTED

### Phase 5: CRM/Portal
- [ ] SuiteDash integration
- [ ] E-sign tracking
- [ ] Client portal

### Phase 6: RPA
- [ ] Power Automate Desktop integration
- [ ] CUA for 24/7 desktop automation
- [ ] ATO portal automation
- [ ] Access Elite automation

### Phase 7: Marketing
- [ ] AI content generation
- [ ] Post scheduling
- [ ] Inclusive language checks

### Phase 8: Communication Coach ⚠️ PARTIAL
- [x] Dashboard Coach tab with Yoodli integration
- [ ] Draft review in workflow
- [ ] Confidence scoring
- [ ] Voice practice mode

### Phase 9: Visual Workflow ⚠️ PLANNED
- [ ] Interactive node-based workflow builder
- [ ] Drag-drop agent orchestration
- [ ] Click nodes to instruct/comment
- [ ] Real-time workflow visualization

---

## 15. CONTACT & OWNERSHIP

- **Owner:** Cherry (the human boss)
- **System Name:** BackPocket OS
- **Product Name:** BackPocketSystem.io
- **Target:** "Smarter Twins" for other accounting firms
- **Infrastructure:** 
  - BPS-Brain-01 (Mini-PC) - runs 24/7
  - BB-Desktop (Windows + RTX GPU) - runs Ollama
  - Synology NAS - file storage

---

## 16. AI MODEL STACK (How the Brains Talk)

See `AI_MODEL_CONFIG.md` for full details.

| Task | Provider | Model | Cost |
|------|----------|-------|------|
| **Me (Coding)** | OpenRouter | Claude 3.5 Sonnet | ~$3/1M |
| **Email Triage** | Google Gemini | gemini-2.0-flash | Free tier |
| **Draft Writing** | Google Gemini | gemini-2.5-flash | Cheap |
| **Fallback (Private)** | Ollama local | Qwen3-8B | FREE |
| **Heavy Tasks** | Ollama GPU | Qwen3-32B | FREE |
| **Communication Coach** | OpenRouter | GPT-4o | ~$5/1M |

**Fallback Chain:** Claude → GPT-4o → Gemini → Ollama → Default

---

## 17. STARTER PROMPT (Copy-Paste for New Chats)

See `STARTER_PROMPT.md` for the full friendly prompt to copy-paste.

**Quick version:**
```
Hey! Working on BackPocket OS. Here's what I need: [YOUR REQUEST]

Remember:
- Read SYSTEM_CONTEXT.md first
- Explain like I'm 5
- Tell me productization impact
- Self-test after changes
```

---

*This file is my memory. Every time I work on this project, I read this first.*
