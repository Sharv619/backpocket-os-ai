# BackPocket OS — Product Requirements Document (PRD)

**Version:** 1.0  
**Date:** 2026-04-14  
**Status:** Draft  
**Owner:** Product Manager / Founder

---

## 1. Executive Summary

### 1.1 Product Name
**BackPocket OS** — AI-powered System of Record for Australian tradies

### 1.2 One-Line Pitch
> Pip handles the admin so Steve can run the tools.

### 1.3 Problem Statement
Solo and small-tradie operators (2-3 person teams) spend 14+ hours/week on admin — quoting, invoicing, email follow-ups, and paperwork. This non-billable time causes burnout, relationship strain, and lost revenue. Existing SaaS tools are expensive, cloud-only (data not owned by user), and require keyboard-centric workflows that don't work on job sites.

### 1.4 Solution
A local-first, voice-first business management system where:
- **Pip** (AI assistant) handles admin via voice commands
- **Local-first** means data stays on user's device/server — not hostage to cloud pricing
- **Human-in-the-loop** ensures every AI output is reviewed before sending

### 1.5 Target Market
- **Geography:** Australia (Western Sydney → national)
- **Segment:** Solo/duo tradies in plumbing, electrical, carpentry, tiling
- **Age:** 28-55 years old
- **Revenue:** $200K-$800K annually
- **Pain:** Hates admin, partner usually handles books, uses phone primarily

---

## 2. Product Vision

### 2.1 North Star
> **Build the tool Steve would want his daughter to use if she became a tradie.**

### 2.2 Core Value Proposition
| Value | Description |
|-------|-------------|
| **Time Back** | 13 hours/week recovered (quantifiable) |
| **Data Ownership** | Local-first — user's data stays theirs |
| **Privacy** | No cloud AI unless user chooses |
| **Simplicity** | Voice-first, no keyboard required |

### 2.3 Three-Year Vision
- 5,000 active users in Australia
- $6M ARR
- 85%+ gross margins
- Category leader in solo-tradie segment

---

## 3. User Stories

### 3.1 Steve (Primary Persona)
| ID | Story | Priority |
|----|-------|----------|
| ST-01 | As a tradie, I want to dictate a quote while driving so I can send it before reaching the next job | P0 |
| ST-02 | As a tradie, I want AI-drafted replies to urgent emails that I can approve with one tap | P0 |
| ST-03 | As a tradie, I want my data stored locally so if the app shuts down I still have my business records | P0 |
| ST-04 | As a tradie, I want before/after photos to automatically become social media posts | P1 |
| ST-05 | As a tradie, I want all my leads, quotes, and payments visible in Google Sheets ("Business OS") | P1 |
| ST-06 | As a tradie, I want to speak instead of type when entering site notes | P2 |

### 3.2 Secondary Personas

#### Partner (Bookkeeper)
| ID | Story | Priority |
|----|-------|----------|
| PT-01 | As a partner who handles books, I want all quotes and invoices in a spreadsheet I can export | P1 |
| PT-02 | As a partner, I want to see when payments are overdue without asking Steve | P2 |

---

## 4. Functional Requirements

### 4.1 Core Features

#### F1: Voice-to-Quote
- **Input:** Voice transcript via mobile app or dictation
- **Processing:** AI extracts job type, materials, labor estimate
- **Output:** Structured quote draft (line items, labor hours, GST)
- **Approval:** User reviews and approves before sending
- **Integration:** Syncs to Google Sheets

#### F2: Peace of Mind Inbox
- **Input:** Incoming emails (Gmail integration)
- **Processing:** AI prioritizes by urgency (Tier 1-4), drafts responses
- **Display:** Dashboard with sender, subject, preview, confidence score
- **Actions:** Approve & Send / Revise / Discard
- **Logging:** All actions logged to audit_log

#### F3: Lead Management
- **Capture:** Manual entry or voice-to-lead conversion
- **Fields:** Client name, email, phone, job type, location, urgency, budget
- **Status:** New → Quoted → Won/Lost
- **Sync:** Auto-creates row in Google Sheets "Leads" sheet

#### F4: Quote & Invoice Generation
- **Input:** From voice transcript or manual entry
- **Output:** ATO-compliant tax invoice (GST, ABN, description)
- **Retention:** 5-year minimum per ATO requirement
- **Disclaimer:** "Pip's suggestions are drafts. You're the tradie; you sign off."

#### F5: Payment Tracking
- **Input:** Manual or voice entry
- **Fields:** Quote ID, amount, date, status
- **Sync:** Updates Google Sheets "Payments" sheet
- **Overdue:** Flags quotes older than 30 days

#### F6: Photo-to-Post
- **Input:** Before/after photos
- **Processing:** AI analyzes materials, generates caption
- **Output:** Draft social media post (optimized for Instagram/Facebook)
- **Approval:** User reviews before auto-post or manual post

#### F7: Google Sheets Sync ("Business OS")
- **Sheets:** Leads, Quotes, Payments, Activities, Twin_Instructions
- **Sync:** Real-time push on create/update
- **Access:** Read-only for partner/bookkeeper

### 4.2 AI Requirements

#### F8: 3-Tier Fallback
| Tier | Provider | Use Case |
|------|----------|----------|
| 1 | Ollama (local) | Primary — fastest, cheapest, most private |
| 2 | OpenRouter | Fallback #1 — cloud LLM |
| 3 | Gemini native | Fallback #2 — final fallback |

#### F9: Human-in-the-Loop (HITL)
- **Mandatory:** No outbound action (email, quote, post) without user approval
- **Architectural:** Enforced in code, not policy
- **Override:** No "auto-approve after X hours" option ever

#### F10: RAG (Retrieval-Augmented Generation)
- **Purpose:** AI learns from user's corrections
- **Storage:** PGVector (PostgreSQL) or ChromaDB
- **Data:** Corrections table, session memory, knowledge base

### 4.3 Technical Requirements

#### F11: PWA (Progressive Web App)
- **Installable:** Add to home screen on iOS/Android
- **Offline:** Service worker caches core UI
- **Push:** Future — push notifications for urgent emails

#### F12: Local-First Data
- **Storage:** SQLite (local) → PostgreSQL (self-hosted)
- **Backup:** Optional cloud sync, user-controlled
- **Export:** JSON bundle for data portability

#### F13: Multi-Tenant Ready (Future)
- **Auth:** Supabase or Clerk for user accounts
- **RLS:** Row-Level Security in PostgreSQL
- **Isolation:** Per-user data encryption

---

## 5. Non-Functional Requirements

### 5.1 Performance
| Metric | Target |
|--------|--------|
| Voice-to-quote | < 60 seconds end-to-end |
| Page load | < 3 seconds |
| API response | < 500ms |
| Uptime | 99.9% |

### 5.2 Security
| Requirement | Implementation |
|-------------|----------------|
| Data at rest | Encrypted (Fernet per user) |
| Data in transit | TLS 1.3 |
| OAuth tokens | Per-user encrypted storage |
| PII handling | Local-first, minimal cloud exposure |

### 5.3 Compliance
| Framework | Requirement |
|-----------|--------------|
| ATO (Australia) | Tax invoice fields, 5-year retention |
| Privacy Act 1988 | APP 1-13 compliance |
| AI Ethics (AU) | 8 principles adherence |
| GDPR | Defensive posture (not marketed to EU) |

---

## 6. User Interface

### 6.1 Screens
| Screen | Purpose |
|--------|---------|
| Dashboard | Overview of pending, leads, pipeline |
| Inbox | Peace of Mind Inbox — pending approvals |
| Leads | Lead list with status filters |
| Quotes | Quote list with status |
| Payments | Payment tracking |
| Photo-to-Post | Camera + AI-generated caption |
| Settings | API keys, preferences, data export |

### 6.2 Mobile-First Design
- Large touch targets (min 44px)
- Voice input prominent
- Minimal text entry
- Dark/light theme support

---

## 7. Pricing Model

### 7.1 Tiers
| Tier | Price | What's Included |
|------|-------|-----------------|
| **The Engine** | $299 one-off | Local-first install, System of Record, lifetime license |
| **The Fuel** | $15/month | AI processing credits (Pip), voice, transcription |

### 7.2 Rationale
- **One-off** = ownership, not rental (tradies hate rent)
- **$15/mo** = below "cancel on a bad day" threshold
- **High upfront** = profitable from Day 1

### 7.3 Unit Economics
| Metric | Year 1 | Year 3 |
|--------|--------|--------|
| Users | 300 | 5,000 |
| ARR | $108K | $6M |
| Gross Margin | ~70% | 85%+ |
| CAC | < $80 | < $120 |
| LTV:CAC | 10:1 | 7:1 |

---

## 8. Go-to-Market

### 8.1 Phases

#### Phase 1: Design Partners (Weeks 0-8)
- 10 Pioneers (free Engine + 12 months Fuel)
- Source: Parramatta Chamber, WhatsApp groups, founder network
- Goal: 3 case studies with hard numbers

#### Phase 2: Paid Pilot (Weeks 9-16)
- $199 one-off + $15/mo (founder pricing)
- 100 customers
- Channels: Facebook Groups, TikTok, trade suppliers

#### Phase 3: Scale (Weeks 17-52)
- Raise to $299 + $15/mo
- 1,000 customers
- Expand to Melbourne, Queensland, Perth

### 8.2 Channels
| Channel | % Budget | Rationale |
|---------|----------|-----------|
| Founder-led sales | 40% | Zero CAC, highest trust |
| TikTok/Reels | 25% | Target audience behavior |
| Facebook Groups | 20% | Native to segment |
| Trade suppliers | 10% | High-intent touchpoint |
| SEO/Content | 5% | Long-tail compounding |

---

## 9. Competitive Landscape

### 9.1 Competitors
| Competitor | Price | Weakness |
|------------|-------|----------|
| ServiceM8 | $29-169/mo | No local-first, expensive |
| Tradify | $45/mo | Keyboard-only |
| AroFlo | $99+/mo | Enterprise-heavy |
| "Just email" | $0 | No AI, manual |

### 9.2 Our Moat
1. **Local-first** — Data ownership (competitors can't match)
2. **Voice-first** — Works in the ute, on the job site
3. **Pip character** — Branded, warm, trust-building
4. **Data flywheel** — Corrections improve the AI locally
5. **Distribution** — Word-of-mouth in tradie WhatsApp groups

---

## 10. Risk Register

| ID | Risk | L | I | Mitigation |
|----|------|---|---|------------|
| R-01 | AI hallucination in quotes | 4 | 5 | HITL mandatory approval |
| R-02 | Competitor (ServiceM8) adds AI | 4 | 3 | 18-month window to category-lead |
| R-03 | Pricing resistance | 3 | 3 | Founder pricing for pilot |
| R-04 | Data breach | 2 | 5 | Encryption, local-first architecture |
| R-05 | ATO non-compliance | 2 | 5 | Tax counsel review, disclaimers |

---

## 11. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Paid customers (17 days) | 3 | Stripe webhooks |
| Paid customers (Year 1) | 300 | Revenue |
| Time saved per week | 13 hours | User survey |
| NPS score | > 50 | Post-launch survey |
| Gross margin | > 70% | Financial |

---

## 12. Roadmap

### Phase 1 (MVP — 17 days)
- [x] Voice-to-Quote API
- [x] Inbox with approval workflow
- [x] Lead/Quote/Payment CRUD
- [x] Google Sheets sync
- [x] PWA front-end

### Phase 2 (3 months)
- [ ] PostgreSQL + PGVector migration
- [ ] Multi-tenant auth
- [ ] Photo-to-Post
- [ ] Oracle ARM deployment

### Phase 3 (Year 1)
- [ ] Scale to 300 users
- [ ] Melbourne/Queensland expansion
- [ ] New verticals (landscapers, mechanics)

---

## Appendix

### A. Technology Choices
- **Backend:** FastAPI (Python)
- **Database:** SQLite → PostgreSQL
- **AI:** Ollama (local), OpenRouter, Gemini
- **Vector:** PGVector
- **Frontend:** Vanilla JS SPA + PWA
- **Hosting:** Cloudflare Pages + local server/Tunnel

### B. Documentation
- `docs/business/WORK_BREAKDOWN_STRUCTURE.md`
- `docs/business/STATUS_UPDATE_2026-04-14.md`
- `docs/HOSTING_AUDIT.md`
- `docs/business/AI_GOVERNANCE_HANDBOOK.md`

---

**Document Owner:** Product Manager / Founder  
**Last Updated:** 2026-04-14  
**Next Review:** 2026-04-30