# BackPocket OS - Complete Documentation

Welcome to the BackPocket OS documentation hub. This folder contains comprehensive guides for all features, workflows, and system architecture.

## 📚 Quick Navigation

### Core Features
- [Email Automation](./EMAIL_AUTOMATION.md) - Smart email triage and draft generation
- [Agentic RAG System](./AGENTIC_RAG.md) - AI-powered document analysis with three specialized twins
- [Blog & Content Generation](./BLOG_GENERATION.md) - Narrative storytelling with AI
- [Google Drive Integration](./DRIVE_INTEGRATION.md) - Sync and analyze Drive files

### Workflows & Automation
- [Social Media Posting Workflow](./WORKFLOWS.md#social-media-workflow) - 4-step automation
- [Content Calendar Management](./WORKFLOWS.md#content-calendar-workflow) - 5-step planning system
- [Analytics & Reporting](./WORKFLOWS.md#analytics-workflow) - 4-step insights dashboard
- [Newsletter Campaign Manager](./WORKFLOWS.md#newsletter-workflow) - 5-step distribution system
- **[Construction/Tradie Workflows](./SPECIALIZED_WORKFLOWS.md)** - AI for trades
  - [Lead-to-Scope Extractor](./SPECIALIZED_WORKFLOWS.md#lead-to-scope-extractor-workflow) - Auto-extract client requirements
  - [Tradie Persona Follow-ups](./SPECIALIZED_WORKFLOWS.md#tradie-persona-follow-up-workflow) - Friendly quote follow-ups
  - [Site Note to Action Items](./SPECIALIZED_WORKFLOWS.md#site-note-to-action-items-workflow) - Voice-to-text automation

### Setup & Configuration
- [Installation & Setup](./SETUP.md) - Get BackPocket running
- [API Keys Configuration](./API_KEYS.md) - Configure Google, OpenRouter, and other services
- [Database Schema](./DATABASE_SCHEMA.md) - SQLite tables and relationships

### System Architecture
- [Architecture Overview](./ARCHITECTURE.md) - System design and data flow
- [AI Models & Routing](./AI_MODELS.md) - LLM selection and cost optimization
- [Security & Privacy](./SECURITY.md) - Data handling and API security

### Troubleshooting
- [FAQ & Troubleshooting](./TROUBLESHOOTING.md) - Common issues and solutions

---

## 👥 Team Setup (new contributors — marketing, law, research, engineering)

One-time setup, takes ~2 minutes:

```bash
git clone https://github.com/Sharv619/backpocket-mvp.git
cd backpocket-mvp
npm run setup
```

That installs MCP dependencies, creates the shared knowledge-bank table, and wires up the git hook that auto-logs every merge into `main` for audit (signed with your git author + commit SHA).

Then open OpenCode in the repo. Four MCP servers load automatically from `.mcp.json`:

| Server | Tools | Use for |
|--------|-------|---------|
| `backpocket-leads` | search / get / create leads | Lead intake work |
| `backpocket-quotes` | create quote, templates, overdue list | Quoting + follow-ups |
| `backpocket-pipeline` | pipeline summary, record payment | Ops / reporting |
| `backpocket-knowledge` | save / search / list notes | **Shared team knowledge bank** |

**Rule of thumb:** anything worth referencing later — marketing copy, legal notes, research findings — drop it via the `save_note` tool in the knowledge bank, **or** just merge it into `main` and the post-merge hook captures it for you. Every entry is signed with your git identity so audits are trivial.

Full restructure rationale: [`docs/MCP_RESTRUCTURE_PLAN.md`](./docs/MCP_RESTRUCTURE_PLAN.md).

---

## 🚀 Getting Started

### 1. **Prerequisites**
- Python 3.8+
- Google Cloud Project with APIs enabled
- OpenRouter API key
- Gmail OAuth configured

### 2. **Quick Start**
```bash
cd /home/lade/Hackathons/.git/backpocket-mvp
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Visit: `http://127.0.0.1:8000/static/index.html`

### 3. **Configure Your Sheet**
1. Go to `.env` and find `SPREADSHEET_ID`
2. Copy your Google Sheet ID from the URL
3. Paste into the `.env` file
4. Restart the server

---

## 🧠 The Three Twins (AI Agents)

BackPocket uses three specialized AI agents that learn from your feedback:

| Twin | Purpose | Best For |
|------|---------|----------|
| **Accountant** | Financial & Tax | Invoices, GST, BAS, expense tracking |
| **Auditor** | Compliance & QA | Document review, verification, checks |
| **Admin** | Operations & Workflow | Email triage, scheduling, reminders |

Each twin:
- ✅ Learns from corrections (builds patterns)
- ✅ Accesses historical context via RAG
- ✅ Routes to cost-optimal AI model
- ✅ Generates professional responses

---

## 💰 Cost Optimization

BackPocket intelligently routes API calls to minimize costs:

- **Simple emails** → Template (free)
- **Medium complexity** → Ollama/local (free)
- **Complex requests** → OpenRouter (pay-per-use, but ~80% cheaper than raw API calls)

See [AI Models & Routing](./AI_MODELS.md) for details.

---

## 📖 Key Concepts

### RAG (Retrieval-Augmented Generation)
- Stores documents in ChromaDB vector database
- Retrieves relevant context before generating responses
- Enables AI to reference your business data

### Learned Patterns
- Each correction becomes a learned pattern
- System automatically applies patterns to similar future emails
- Over time, twins get smarter without additional training

### Vision Processing
- Analyze invoices, receipts, and documents
- Extract structured data from images
- Uses free OpenRouter vision models

---

## 🔧 Common Tasks

### Import Real Emails
```bash
python3 import_real_emails.py
```
Fetches your actual Gmail messages and populates the dashboard.

### Sync Google Drive
Via the Dashboard:
1. Go to **📁 DRIVE** section
2. Enter your folder ID
3. Click "Sync to RAG"

Or via API:
```bash
curl -X POST http://127.0.0.1:8000/api/drive/sync-to-rag \
  -H "Content-Type: application/json" \
  -d '{"folder_id":"YOUR_FOLDER_ID","twin_type":"admin"}'
```

### Generate Blog Post
```bash
curl http://127.0.0.1:8000/api/blog/generate?title=My%20Story&theme=entrepreneurship
```

---

## 📞 Support

For detailed information on any topic, see the relevant documentation file in this folder.

**Need help?** Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
