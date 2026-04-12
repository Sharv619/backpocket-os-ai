# BackPocket MVP 🏗️

**AI-powered business automation platform for construction & tradie businesses**

Transform how you manage leads, quotes, and payments with intelligent AI workflows powered by Gmail, Google Drive, and specialized construction tools.

---

## ⚡ Quick Start

### Prerequisites
- Python 3.12+
- pip
- Gmail account (for OAuth)
- OpenRouter API key (optional, for AI features)

### 1. Clone & Setup
```bash
git clone https://github.com/cheri21050/backpocket-mvp.git
cd backpocket-mvp

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Add your API keys:
# - OPENROUTER_API_KEY=sk-or-v1-...
# - GEMINI_API_KEY=...
# - GMAIL_CLIENT_ID=...
# - GMAIL_CLIENT_SECRET=...
```

### 2. Initialize Database
```bash
python3 scripts/create_construction_tables.py
```

### 3. Seed Demo Data (Optional)
```bash
python3 scripts/demo_seed.py
```

### 4. Start Server
```bash
python3 main.py
# OR
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 5. Open Dashboard
Visit **http://127.0.0.1:8000** in your browser

---

## 🎯 Features

### Construction Management
- **📋 Lead Management** - Track incoming jobs with email extraction AI
- **💰 Quote Pipeline** - Generate, send, and track quotes with tradie pricing
- **💳 Payment Tracking** - Record and monitor payments
- **📁 Job Files** - Organize documents by job

### AI-Powered Workflows
- **✉️ Email Triage** - Automatic email categorization
- **🤖 Lead Extraction** - AI extracts job details from emails
- **💬 Tradie Follow-ups** - Friendly, personalized follow-up messages
- **📚 Agentic RAG** - Learn from past decisions with ChromaDB

### Business Workflows
- **📧 Email Rules** - Set up email automation rules
- **📄 Document Management** - Track and organize documents
- **📊 Marketing Activity** - Monitor social media & posts
- **✅ Task Management** - Stay organized with workflow tasks

### MCP Orchestrator
Seamless integration with:
- **Gmail MCP** - Search, draft, send emails
- **Google Drive MCP** - Manage files and organize
- **Google Maps MCP** - Calculate distances & routes
- **BackPocket Local MCP** - 13 tradie-specific tools

---

## 📊 Dashboard Sections

### Construction (Left Sidebar)
- **Leads** - View all leads with status, job type, budget
- **Quotes** - Track quotes through pipeline (draft → sent → accepted)
- **Payments** - Record and monitor payments received

### Workflows (Right Sidebar)
- **Email** - Email rules and automation
- **Documents** - Document tracking and analysis
- **Marketing** - Social media activity and insights
- **Tasks** - Workflow tasks and due dates

---

## 🔗 API Endpoints

### Construction Features
```
POST   /api/construction/leads                    Create lead
GET    /api/construction/leads                    List leads
GET    /api/construction/leads/{id}               Get lead details
PATCH  /api/construction/leads/{id}               Update lead status

POST   /api/construction/quotes                   Create quote
GET    /api/construction/quotes                   List quotes
GET    /api/construction/quotes/{id}              Get quote details
PATCH  /api/construction/quotes/{id}              Update quote status
GET    /api/construction/pipeline                 Pipeline summary

POST   /api/construction/payments                 Record payment
GET    /api/construction/payments                 List payments

POST   /api/construction/leads/extract            AI: Extract lead from email
POST   /api/construction/quotes/{id}/tradie-followup   AI: Generate follow-up
```

### Workflow Features
```
GET    /api/email-rules                           Email automation rules
GET    /api/documents                             Documents
GET    /api/marketing/activity                    Marketing activity
GET    /api/workflow/stages                       Tasks and stages
```

**Full API Reference:** See `API_REFERENCE.md`

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Python 3.12, FastAPI |
| **Database** | SQLite (5 construction tables) |
| **AI/ML** | OpenRouter, Google Gemini, ChromaDB |
| **Cloud APIs** | Gmail OAuth, Google Drive, Google Sheets |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Orchestration** | Model Context Protocol (MCP) |

---

## 📁 Project Structure

```
backpocket-mvp/
├── main.py                          # FastAPI app (4300+ lines, 101 endpoints)
├── services/                        # Business logic modules
│   ├── construction.py             # Lead/quote/payment management
│   ├── gemini.py                   # AI model integration
│   ├── gmail.py                    # Gmail OAuth & email processing
│   ├── database.py                 # SQLite schema & queries
│   ├── agentic_rag.py             # Vector DB & learned patterns
│   └── ... (12+ more services)
├── scripts/                         # Database & demo utilities
│   ├── create_construction_tables.py
│   └── demo_seed.py
├── src/mcp-wrapper/                # MCP orchestrator server
│   └── server.js                   # Node.js MCP server (13 tools)
├── static/                         # Frontend
│   ├── index.html                 # Dashboard (4500+ lines)
│   └── *.png                      # Background images
├── docs/                           # Documentation
│   ├── MCP_ORCHESTRATOR.md
│   ├── API_REFERENCE.md
│   └── ...
└── .env                           # API keys (DO NOT COMMIT)
```

---

## 🎓 How It Works

### Lead Creation Flow
1. Email arrives → Gmail MCP captures it
2. BackPocket Local MCP extracts job details using AI
3. **Lead created** in database with:
   - Client name, email, job type
   - Location, urgency, estimated budget
4. Dashboard shows new lead immediately

### Quote Generation Flow
1. User creates quote from lead
2. System calculates:
   - Materials cost + Labor ($150/hr) + Markup (20%)
3. **Quote created** with total amount
4. AI generates friendly tradie-style follow-up message
5. User sends via email

### Payment Tracking
1. Client pays
2. User records payment amount & date
3. Quote status updates to "paid"
4. Pipeline summary updates automatically

---

## 🔐 Security

- API keys stored in `.env` (never committed)
- Gmail OAuth 2.0 for secure email access
- Input validation on all endpoints
- CORS headers configured
- No hardcoded credentials in code

**For Production:**
- Migrate to PostgreSQL
- Use environment variables via hosting platform
- Enable HTTPS
- Add authentication middleware
- Implement rate limiting

---

## 📈 Stats

| Metric | Value |
|--------|-------|
| **Lines of Code** | 57,939 |
| **API Endpoints** | 101 |
| **Database Tables** | 22+ |
| **Python Modules** | 17 |
| **MCP Tools** | 13 |
| **Frontend Sections** | 8 |

---

## 🧪 Testing

### Manual Testing
```bash
# Create a lead
curl -X POST http://127.0.0.1:8000/api/construction/leads \
  -H "Content-Type: application/json" \
  -d '{"client_name":"John","email":"john@example.com","job_type":"Kitchen","location":"Sydney","urgency":"high","estimated_budget":15000}'

# Get all leads
curl http://127.0.0.1:8000/api/construction/leads

# Create a quote
curl -X POST http://127.0.0.1:8000/api/construction/quotes \
  -H "Content-Type: application/json" \
  -d '{"lead_id":1,"materials_cost":8000,"labor_hours":5,"markup_percent":20}'
```

### Dashboard Testing
1. Open http://127.0.0.1:8000
2. Click sections in sidebar to load data
3. Click "Refresh" buttons to reload
4. Check browser console for errors (F12)

---

## 📚 Documentation

- **[CLAUDE.md](.claude/CLAUDE.md)** - Architecture & development guide
- **[API_REFERENCE.md](API_REFERENCE.md)** - Complete endpoint documentation
- **[MCP_ORCHESTRATOR.md](docs/MCP_ORCHESTRATOR.md)** - MCP system guide
- **[PROJECT_AUDIT_REPORT.md](PROJECT_AUDIT_REPORT.md)** - Comprehensive audit

---

## 🚀 Deployment

### Local Development
```bash
python3 main.py
# Runs on http://127.0.0.1:8000
```

### Vercel
```bash
# Already configured in vercel.json
vercel deploy
```

### Docker
```bash
docker build -t backpocket .
docker run -p 8000:8000 backpocket
```

---

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Commit changes: `git commit -m "Add feature"`
3. Push to GitHub: `git push origin feature/your-feature`
4. Create Pull Request

---

## 📋 Roadmap

### Phase 1-5: MVP ✅ COMPLETE
- Construction features (leads, quotes, payments)
- AI integration (lead extraction, follow-ups)
- Dashboard UI (8 sections)
- MCP orchestrator
- Comprehensive documentation

### Phase 6: Production Hardening
- [ ] Unit test suite (pytest)
- [ ] Structured logging (JSON)
- [ ] Rate limiting
- [ ] PostgreSQL migration

### Phase 7: Feature Expansion
- [ ] Email notifications
- [ ] Invoice OCR processing
- [ ] Slack integration
- [ ] Calendar blocking
- [ ] Mobile app (Flutter/React Native)

---

## 🆘 Troubleshooting

### Server won't start
```bash
# Kill existing process
pkill -f "python3 main.py"

# Check port is free
lsof -i :8000

# Restart
python3 main.py
```

### Database errors
```bash
# Recreate database
rm backpocket.db
python3 scripts/create_construction_tables.py
```

### API errors
1. Check `.env` has all required keys
2. Check network/firewall
3. Read browser console (F12)
4. Check server logs

---

## 📧 Support

- **Issues?** Open GitHub issue
- **Questions?** Check documentation in `docs/`
- **Bug Report?** Include error log + steps to reproduce

---

## 📄 License

MIT License - See LICENSE file for details

---

## 👥 Team

**Developed with ❤️ for construction & tradie businesses**

- **Hackathon Project**: BackPocket MVP
- **Status**: Production Ready
- **Last Updated**: April 12, 2026

---

**Ready to automate your tradie business? Start the server and open http://127.0.0.1:8000** 🚀
