# SYSTEM_INVENTORY_MASTER.md

## 1. Hardware Infrastructure (The "Two-Brain" Setup)

| Device       | Role          | Specs                                     | IP Address    | Status |
|--------------|---------------|-------------------------------------------|---------------|--------|
| BPS-Brain-01 | Orchestrator  | Mini-PC, Intel N150, 16GB RAM, 512GB SSD  | 192.168.0.25  | Active |
| BB-Desktop   | Heavy Lifter  | Windows, i7-11700F, 64GB RAM, RTX GPU    | 192.168.0.12  | Active |
| Synology NAS | Memory/Filing | DS420j, 20TB+ Storage                     | 192.168.0.2   | Active |

---

## 2. Software & AI Stack (The "Nervous System")

### A. Orchestration Layer (Runs on BPS-Brain-01)
- **Platform:** Docker + Portainer (Container Management)
- **Workflow Engine:** n8n or Activepieces (Self-hosted)
- **Database:** PostgreSQL (State Memory, Deduplication, Audit Logs)
- **Purpose:** 24/7 email polling, WhatsApp notifications, Google Sheets/NAS integration

### B. AI Brain Layer (Runs on BB-Desktop)
- **AI Engine:** Ollama (Local LLM Server)
- **Models:**
  - Qwen3-8B: Fast daily email triage and categorization
  - Qwen3-32B (or QwQ): Complex tax reasoning, invoice extraction, "thinking" tasks
- **OCR Engine:** OCRmyPDF / Tesseract (document intelligence)
- **Purpose:** Local, private, no-subscription intelligence

### C. Integration Layer (The "Hands")
- **Email:** Gmail API (2x inboxes) + Microsoft Graph/Outlook API (1x inbox)
- **Sheets:** Google Sheets API (System of Identity + Email Log)
- **Remote Access:** Getscreen.me (Headless management)
- **UI Automation:** Power Automate Desktop (legacy desktop apps like Access Elite)

---

## 3. The "Digital Twin" Operational Logic

### The Tri-Layer Triage Strategy
1. **Layer 0 (Rules):** Python logic filters Spam/Polite Noise/Notifications (bypasses AI)
2. **Layer 1 (Batch AI):** n8n/Activepieces batches emails to Gemini/Ollama for categorization
3. **Layer 2 (Local Fallback):** If Gemini fails, falls back to local Qwen3 on BB-Desktop

### The "Human-in-the-Loop" Guardrails
- **Draft-Only Policy:** AI creates drafts; never sends emails automatically
- **Approval Gates:** WhatsApp notifications require "Approve/Reject" for all client-facing actions
- **Identity Protection:** Sheet 1 (Client Master) is source of truth; unmatched senders flagged for review

---

## 4. BACKPOCKET OS MODULE INVENTORY

### 📨 EMAIL MODULE
| Component | File | Status | Notes |
|-----------|------|--------|-------|
| Triage Engine | `services/email/triage.py` | Ready | 5-tier sorting |
| Gmail Connector | `services/email/gmail.py` | Ready | Gmail API |
| IMAP Connector | `services/email/imap.py` | Ready | Outlook/IMAP |
| Deduplication | `services/email/dedup.py` | Ready | SQLite-based |
| Client Matching | `services/email/client_match.py` | Ready | Sheets lookup |

### 📄 DOCUMENTS MODULE
| Component | File | Status | Notes |
|-----------|------|--------|-------|
| OCR Engine | `services/documents/ocr.py` | TODO | Tesseract/OCRmyPDF |
| Classifier | `services/documents/classifier.py` | TODO | AI-based |
| Field Extractor | `services/documents/extractor.py` | TODO | Regex + AI |
| Encode Queue | `services/documents/encode_queue.py` | TODO | SQLite tracking |

### 💰 ACCOUNTING MODULE
| Component | File | Status | Notes |
|-----------|------|--------|-------|
| QBO Connector | `services/accounting/qbo.py` | TODO | QuickBooks API |
| Xero Connector | `services/accounting/xero.py` | TODO | Xero API |
| MYOB Connector | `services/accounting/myob.py` | TODO | MYOB API |
| Reconciliation | `services/accounting/reconciliation.py` | TODO | Bank matching |

### 👥 CRM/PORTAL MODULE
| Component | File | Status | Notes |
|-----------|------|--------|-------|
| SuiteDash | `services/crm/suitedash.py` | TODO | Portal API |
| E-Sign | `services/crm/esign.py` | TODO | DocuSign/HelloSign |
| Client Portal | `services/crm/client_portal.py` | TODO | Access control |

### 🤖 RPA MODULE
| Component | File | Status | Notes |
|-----------|------|--------|-------|
| Power Automate | `services/rpa/power_automate.py` | TODO | Desktop flows |
| ATO Portal | `services/rpa/ato_portal.py` | TODO | Government sites |
| Access Elite | `services/rpa/elite_access.py` | TODO | Legacy DB |

### 📢 MARKETING MODULE
| Component | File | Status | Notes |
|-----------|------|--------|-------|
| Content Gen | `services/marketing/content_gen.py` | TODO | AI drafts |
| Scheduler | `services/marketing/scheduler.py` | TODO | Queue posts |
| Social AI | `services/marketing/social_ai.py` | TODO | Platform APIs |

### 🛡️ GOVERNANCE MODULE
| Component | File | Status | Notes |
|-----------|------|--------|-------|
| Audit Log | `services/governance/audit_log.py` | TODO | All actions |
| Risk Flags | `services/governance/risk_flags.py` | TODO | Anomaly detection |
| Compliance | `services/governance/compliance.py` | TODO | Rule checks |

### 🎤 COMMUNICATION COACH MODULE
| Component | File | Status | Notes |
|-----------|------|--------|-------|
| Draft Review | `services/coach/review.py` | TODO | Main coach logic |
| Authority Check | `services/coach/authority_check.py` | TODO | Weak language detector |
| Clarity Check | `services/coach/clarity_check.py` | TODO | CTA verification |
| Empathy Check | `services/coach/empathy_check.py` | TODO | Tone analyzer |
| Power Version | `services/coach/power_version.py` | TODO | Rewrite generator |
| Confidence Score | `services/coach/confidence_score.py` | TODO | Rating system |
| Voice Practice | `services/coach/voice_practice.py` | TODO | TTS/STT integration |

---

## 5. Configuration Files (Config-Driven, NOT Hard-Coded)

| File | Purpose | Location |
|------|---------|----------|
| `tiers.json` | Email tier rules | `config/` |
| `templates/*.html` | Email draft templates | `config/templates/` |
| `document_rules.json` | Document classification | `config/documents/` |
| `accounting_map.json` | QBO/Xero/MYOB mappings | `config/accounting/` |
| `coach_rules.json` | Communication style rules | `config/coach/` |
| `settings.json` | System-wide settings | `config/` |
| `.env` | API keys, secrets | Root |

---

## 6. Maintenance & Productization Protocol

### Maintenance (The "Headless" Setup)
- **Auto-Login:** Enabled via netplwiz (Local Account)
- **Power:** BIOS set to "Power On after AC Loss"
- **Updates:** Windows Update set to "Manual" (via WUB)
- **Access:** Getscreen.me (2FA enabled)

### Productization Strategy (BackPocketSystem.io)
- **Modular Design:** Workflows in small, reusable chunks (Intake -> Triage -> Filing -> Logging)
- **Configuration-Driven:** Rules, categories, templates in Google Sheets/JSON, not hard-coded
- **Deployment:** Containerized (Docker) for "one-click" installation for future clients
- **Per-Module Installation:** Each module can be installed independently

---

## 7. DEPENDENCY MAP

```
                    ┌─────────────────────────────────────────┐
                    │         BACKPOCKET OS CORE              │
                    │  (main.py, database.py, sheets.py)      │
                    └─────────────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   AI LAYER      │       │ COMMUNICATION   │       │   STORAGE       │
│ (gemini,ollama) │       │ (whapi, notif)  │       │ (NAS, Sheets)   │
└─────────────────┘       └─────────────────┘       └─────────────────┘
          │                           │                           │
          └───────────────────────────┼───────────────────────────┘
                                      │
    ┌─────────┬─────────┬─────────┬───┴───┬─────────┬─────────┐
    │         │         │         │       │         │         │
    ▼         ▼         ▼         ▼       ▼         ▼         ▼
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
│ EMAIL │ │ DOCS  │ │ ACCT  │ │  CRM  │ │  RPA  │ │ MKTG  │ │ COACH │
└───────┘ └───────┘ └───────┘ └───────┘ └───────┘ └───────┘ └───────┘
```

---

## 8. HEALTH CHECK ENDPOINTS

| Module | Endpoint | What It Checks |
|--------|----------|----------------|
| Core | `GET /health` | Server running |
| Email | `GET /health/email` | Gmail + IMAP connectivity |
| AI | `GET /health/ai` | Gemini + Ollama responsiveness |
| WhatsApp | `GET /health/whatsapp` | Whapi.cloud connectivity |
| Sheets | `GET /health/sheets` | Google Sheets API |
| NAS | `GET /health/nas` | Synology NAS connectivity |

---

*Last Updated: 2026-03-27*
*Version: 2.0*
