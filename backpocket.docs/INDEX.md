# BackPocket Documentation Index

Complete navigation guide for all BackPocket documentation.

---

## 🚀 Getting Started

**New to BackPocket?** Start here:

1. **[QUICK_START.md](./QUICK_START.md)** - Get running in 5 minutes
2. **[SETUP.md](./SETUP.md)** - Full installation guide
3. **[API_KEYS.md](./API_KEYS.md)** - Configure all external services

---

## 📚 Feature Documentation

### Email & Automation
- [Email Automation Guide](./README.md#email-automation) - Smart email triage
- [AI Drafting System](./README.md#ai-drafts) - Auto-generate professional responses
- [Learned Patterns](./README.md#learned-patterns) - AI that improves over time

### Content & Blog
- [Blog Generation](./BLOG_GENERATION.md) - AI-powered narrative storytelling
- [Content Calendar](./WORKFLOWS.md#content-calendar-workflow) - Plan & publish content

### Data Integration
- [Google Sheets Integration](./README.md#sheets-integration) - Sync business data
- [Google Drive Integration](./DRIVE_INTEGRATION.md) - File syncing & analysis
- [Document Vision](./README.md#cloud-vision) - Analyze invoices & documents

### AI Agents
- [Agentic RAG System](./AGENTIC_RAG.md) - Multi-agent orchestration
- [The Three Twins](./README.md#the-three-twins) - Accountant, Auditor, Admin

---

## 🔧 Workflows & Automation

### Standard Business Workflows
1. **[Social Media Posting](./WORKFLOWS.md#social-media-workflow)** (4 steps)
   - Content input → Drafting → Review → Publish
2. **[Content Calendar](./WORKFLOWS.md#content-calendar-workflow)** (5 steps)
   - Planning → Themes → Drafts → Review → Auto-publish
3. **[Analytics & Reporting](./WORKFLOWS.md#analytics-workflow)** (4 steps)
   - Connect → Define KPIs → Auto-analysis → Reports
4. **[Newsletter Campaigns](./WORKFLOWS.md#newsletter-workflow)** (5 steps)
   - Setup → Content → Design → Preview → Send & Track

### Construction/Tradie Workflows
1. **[Lead-to-Scope Extractor](./SPECIALIZED_WORKFLOWS.md#lead-to-scope-extractor-workflow)**
   - Auto-extract client requirements from emails
   - Feeds into quote generation
2. **[Tradie Persona Follow-ups](./SPECIALIZED_WORKFLOWS.md#tradie-persona-follow-up-workflow)**
   - Friendly, professional quote follow-ups
   - Sounds like a real person, not a bot
3. **[Site Note to Action Items](./SPECIALIZED_WORKFLOWS.md#site-note-to-action-items-workflow)**
   - Convert voice memos to structured reports
   - Auto-generate material lists & action items

---

## 📖 Core Guides

### Architecture & Design
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System design & data flow
- **[AI_MODELS.md](./AI_MODELS.md)** - LLM selection & cost optimization
- **[DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md)** - 22+ table definitions

### Security & Operations
- **[SECURITY.md](./SECURITY.md)** - Data handling & API security
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Run in production
- **[MONITORING.md](./MONITORING.md)** - Uptime & health checks

---

## 🚨 Troubleshooting & Support

**Having issues?** Check these in order:

1. **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - Common problems & fixes
   - Server issues (port conflicts, module errors)
   - Gmail & email problems
   - Google Sheets configuration
   - Database issues
   - API & integration problems
   - Dashboard/frontend issues

2. **[API_KEYS.md](./API_KEYS.md#troubleshooting)** - API key issues
   - OpenRouter errors
   - Gmail OAuth problems
   - Google Sheets access

3. **[FAQ.md](./FAQ.md)** - Frequently asked questions

---

## 🔑 API & Integration Reference

- **[API_KEYS.md](./API_KEYS.md)** - All API setup & testing
  - OpenRouter (LLM)
  - Google APIs (Gmail, Sheets, Drive)
  - Optional: WHAPI, ElevenLabs, Ollama

- **[API_REFERENCE.md](./API_REFERENCE.md)** - Complete endpoint documentation
  - Email endpoints
  - Draft generation
  - Blog generation
  - Drive integration
  - Construction workflows

---

## 📋 Quick Reference Tables

### Files Overview
| File | Purpose | Read Time |
|------|---------|-----------|
| [QUICK_START.md](./QUICK_START.md) | 5-min setup | 5 min |
| [SETUP.md](./SETUP.md) | Full install | 15 min |
| [README.md](./README.md) | Feature overview | 10 min |
| [WORKFLOWS.md](./WORKFLOWS.md) | Business automation | 30 min |
| [SPECIALIZED_WORKFLOWS.md](./SPECIALIZED_WORKFLOWS.md) | Construction workflows | 25 min |
| [API_KEYS.md](./API_KEYS.md) | API configuration | 15 min |
| [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) | Fix problems | 10 min |

### Services & Keys
| Service | Purpose | Setup Time | Cost |
|---------|---------|-----------|------|
| OpenRouter | LLM for drafts | 2 min | ~$0.01/request |
| Gmail | Email auth | 5 min | Free |
| Google Sheets | Data sync | 5 min | Free |
| Google Drive | File sync | 2 min | Free |
| Gemini | Backup LLM | 2 min | Free tier |
| WHAPI | SMS/WhatsApp | 5 min | ~$0.01/msg |
| ElevenLabs | Voice | 2 min | Free tier |
| Ollama | Local AI | 10 min | Free |

---

## 🎯 Common Paths Through Docs

### "I just installed BackPocket"
1. [QUICK_START.md](./QUICK_START.md)
2. [README.md](./README.md) - Overview of features
3. Explore the dashboard

### "I'm having issues"
1. [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
2. Check specific guide (API_KEYS, SETUP, etc.)
3. Re-run test scripts

### "I want to build workflows"
1. [WORKFLOWS.md](./WORKFLOWS.md) - Standard workflows
2. [SPECIALIZED_WORKFLOWS.md](./SPECIALIZED_WORKFLOWS.md) - Construction workflows
3. [API_REFERENCE.md](./API_REFERENCE.md) - See available endpoints

### "I want to understand the system"
1. [ARCHITECTURE.md](./ARCHITECTURE.md) - System design
2. [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) - Data structure
3. [AI_MODELS.md](./AI_MODELS.md) - How AI routing works

### "I want to deploy to production"
1. [SETUP.md](./SETUP.md) - Installation
2. [DEPLOYMENT.md](./DEPLOYMENT.md) - Production setup
3. [SECURITY.md](./SECURITY.md) - Secure configuration
4. [MONITORING.md](./MONITORING.md) - Health checks

---

## 💡 Key Concepts

### The Three Twins
BackPocket uses three AI agents that specialize in different areas:

- **Accountant Twin**: Invoices, taxes, GST, expenses, quotes
- **Auditor Twin**: Compliance, document review, verification
- **Admin Twin**: Email triage, scheduling, operations

Each learns from your feedback and applies patterns to future work.

### Learned Patterns
When you correct an AI response, the system learns:
- Similar emails in future → patterns applied automatically
- Over time, AI gets better at your specific business

### Cost Optimization
BackPocket saves money by intelligently routing API calls:
- Simple requests → Template (free)
- Medium → Ollama local AI (free, if available)
- Complex → OpenRouter (cheapest LLM routing)

### RAG (Retrieval-Augmented Generation)
AI references your documents before responding:
- Stores documents in vector database
- Retrieves relevant context
- Generates more accurate, contextual responses

---

## 🔗 External Resources

### Google Cloud
- [Google Cloud Console](https://console.cloud.google.com/) - Create projects
- [Gmail API Docs](https://developers.google.com/gmail/api/guides) - Reference
- [Google Sheets API](https://developers.google.com/sheets/api) - Reference
- [Google Drive API](https://developers.google.com/drive/api) - Reference

### AI Services
- [OpenRouter](https://openrouter.ai/) - LLM routing platform
- [Google Gemini](https://ai.google.dev/) - Backup model
- [Ollama](https://ollama.ai/) - Local LLM
- [ElevenLabs](https://elevenlabs.io/) - Text-to-speech

### Communities
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLite Reference](https://www.sqlite.org/docs.html)
- [ChromaDB Docs](https://docs.trychroma.com/)

---

## 📝 Document Versions

| Document | Updated | Version |
|----------|---------|---------|
| README.md | 2024-04 | 1.0 |
| QUICK_START.md | 2024-04 | 1.0 |
| SETUP.md | 2024-04 | 1.0 |
| WORKFLOWS.md | 2024-04 | 1.0 |
| SPECIALIZED_WORKFLOWS.md | 2024-04 | 1.0 |
| API_KEYS.md | 2024-04 | 1.0 |
| TROUBLESHOOTING.md | 2024-04 | 1.0 |

---

## 🎓 Learning Path

**Beginner** (Time investment: 30 min)
1. QUICK_START.md
2. README.md (overview section)
3. Explore dashboard

**Intermediate** (Time: 2 hours)
1. SETUP.md
2. WORKFLOWS.md
3. Try building a workflow

**Advanced** (Time: 4+ hours)
1. ARCHITECTURE.md
2. DATABASE_SCHEMA.md
3. API_REFERENCE.md
4. Build custom integrations

**Expert** (Time: 8+ hours)
1. Study all guides
2. Read source code
3. Build custom agents
4. Deploy to production

---

## 📞 Need Help?

1. **Check docs** - Most answers are here
2. **Check TROUBLESHOOTING.md** - For specific errors
3. **Test components** - Use provided test scripts
4. **Check logs** - Server output has detailed error info
5. **Re-read API_KEYS.md** - 90% of issues are API setup

---

**Last Updated**: April 2024  
**Total Documentation**: ~50 pages  
**Estimated Read Time**: 4-6 hours (all docs)
