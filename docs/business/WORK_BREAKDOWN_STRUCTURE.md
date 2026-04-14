# BackPocket OS — Work Breakdown Structure

**Generated:** 2026-04-13  
**Horizon:** 17-Day Sprint (Apr 13–30) + Year 1 Roadmap

---

## 🎯 TEAM: IT (Technical)

**Owner:** CTO / Fractional CTO  
**Focus:** Infrastructure, AI pipeline, data layer, security, compliance engineering

### EPIC A — Foundation (Days 1–3)
| Task | Description | Owner |
|------|-------------|-------|
| A1 | Oracle ARM provisioning script | IT Engineer |
| A2 | GitHub Actions deploy workflow | IT Engineer |
| A3 | Auth IdP ADR (Supabase vs Clerk) | IT Engineer |
| A4 | Backup to R2 script | IT Engineer |

### EPIC E — Data Layer (Days 1–7)
| Task | Description | Owner |
|------|-------------|-------|
| E1 | SQLite to Postgres migration script | IT Engineer |
| E2 | services/postgres_db.py (SQLAlchemy) | IT Engineer |
| E3 | services/pgvector_rag.py | IT Engineer |
| E4 | Dual-write logic | IT Engineer |

### EPIC F — Auth + RLS (Days 4–10)
| Task | Description | Owner |
|------|-------------|-------|
| F1 | IdP integration code | IT Engineer |
| F2 | RLS policies | IT Engineer |
| F3 | Token encryption (Fernet) | IT Engineer |
| F4 | Caddy security headers | IT Engineer |

### EPIC G — Photo-to-Post (Days 8–13)
| Task | Description | Owner |
|------|-------------|-------|
| G1 | Flutter camera UI | Minimax |
| G2 | /api/vision/analyze_materials endpoint | Minimax |
| G3 | /api/social/generate_post endpoint | Minimax |
| G4 | Flutter social post review UI | Minimax |

### EPIC H — Security (Days 11–17)
| Task | Description | Owner |
|------|-------------|-------|
| H1 | Privacy policy / TOS drafts | IT Engineer |
| H2 | OWASP ZAP automation | IT Engineer |
| H3 | CIS benchmark hardening | IT Engineer |

### Ongoing Technical Operations
- **AI Router:** 3-tier fallback maintenance (Ollama → OpenRouter → Gemini)
- **Observability:** Sentry + UptimeRobot monitoring
- **Compliance:** APP 1–13 mapping, ATO invoice validation, NDB runbook

---

## 🎯 TEAM: MARKETING

**Owner:** Product Manager / Founder  
**Focus:** GTM, customer acquisition, brand, content, partnerships

### Phase 1 — Design Partner (Weeks 0–8)
| Task | Description | Timing |
|------|-------------|--------|
| M1 | Recruit 10 "Pioneers" via Parramatta Chamber | Days 1–14 |
| M2 | Weekly feedback calls with Pioneers | Ongoing |
| M3 | Collect 3 case studies with hard numbers | Days 30–56 |

### Phase 2 — Paid Pilot (Weeks 9–16)
| Task | Description | Timing |
|------|-------------|--------|
| M4 | Launch at $199 one-off + $15/mo (founder pricing) | Day 60 |
| M5 | Facebook Groups outreach ("Sydney Tradies Network") | Days 60–90 |
| M6 | TikTok/Reels "Steve-POV" content production | Days 60–90 |
| M7 | Trade supplier partnerships (Reece, Tradelink, Bunnings) | Days 60–90 |
| M8 | Referral program ($50 credit per referral) | Day 60 |

### Phase 3 — Scale (Weeks 17–52)
| Task | Description | Timing |
|------|-------------|--------|
| M9 | Raise pricing to $299 + $15/mo | Day 120 |
| M10 | Open waitlist → drip-launch | Day 120 |
| M11 | Expand to Melbourne, Queensland, Perth | Days 180–365 |
| M12 | Add verticals (landscapers, mobile mechanics) | Days 180–365 |

### Content & Brand
| Task | Description |
|------|-------------|
| C1 | "Pip" character voice-first UX brand guidelines |
| C2 | backpocket.ai/blog SEO content (~"tradie quote template") |
| C3 | Testimonial collection from Pioneer program |

---

## 🎯 TEAM: FINANCE

**Owner:** Product Manager / Founder  
**Focus:** Pricing, unit economics, ATO compliance, funding, insurance

### Pricing & Revenue
| Task | Description | Target |
|------|-------------|--------|
| F1 | Set $299 one-off (Engine) + $15/mo (Fuel) pricing | Launch |
| F2 | Founder pricing $199 for first 100 customers | Pilot |
| F3 | Stripe billing integration (EPIC C) | Day 60 |

### Unit Economics Targets
| Metric | Year 1 | Year 3 |
|--------|--------|--------|
| Active Users | 300 | 5,000 |
| ARR | $108K | $6M |
| Gross Margin | ~70% | 85%+ |
| CAC Target | < $80 | < $120 |
| LTV:CAC | 10:1 | 7:1 |

### Compliance & Legal
| Task | Description | Owner |
|------|-------------|-------|
| FC1 | ATO invoice field validation (GST Act s29-70) | Compliance |
| FC2 | 5-year record retention policy | Compliance |
| FC3 | Non-reliance disclaimer in UI | Compliance |
| FC4 | Not a registered tax agent — ToS disclaimer | Legal |
| FC5 | Cyber insurance $2M bound | Finance |
| FC6 | OAIC NDB notification template (30-day window) | Compliance |

### Funding
| Task | Description | Timing |
|------|-------------|--------|
| FND1 | Seed round preparation (if needed) | Q3 2026 |
| FND2 | Series A or acquisition readiness | Year 3 |

---

## 📊 17-Day Sprint Summary

| Day | IT (EPIC) | Marketing | Finance |
|-----|-----------|-----------|---------|
| 1–3 | A1, A2 | Pioneer recruitment | Pricing finalised |
| 4–7 | B1, B2, F1, E2 | Case study prep | FC1, FC2 |
| 8–12 | C1, G2, G3 | Pilot prep | Stripe (C1) |
| 13–17 | H1, H2, H3, Integration | Go-live | FC4, FC5 |

---

## 📋 Dependencies

```
A1 ──────► A2
 │           │
 └───────────┴─────────────► E1 ──► E2 ──► E3 ──► F2
               │              │              │
               ▼              ▼              ▼
              B1 ──► B2 ──► B3 ◄───► G1 ◄───► G2
               │              │
               └──────────────┴──────────────┴───────► C1
```

---

## 🎯 Success Metrics

| Metric | Target | Measure |
|--------|--------|---------|
| Paid customers | 3 | Stripe webhooks |
| Uptime | 99.9% | Oracle status |
| Voice-to-Quote | <60s | End-to-end timing |
| Photo-to-Post | <30s | End-to-end timing |
| RLS | Active | Postgres policies |
| CAC | < $80 | Marketing spend / customers |
| ARR | $108K (Y1) | Revenue recognition |

---

## 🛠️ Build Your Own Tools — Ideas for Team Members

Based on this project, here are small tools each team can build using OpenCode:

### 🖥️ IT Team — Automation & DevOps Tools
| Tool | What It Does | Use Case |
|------|-------------|----------|
| **Auto-SQL-Migration** | Detects SQLite schema changes → generates Postgres migration scripts | Save hours on E1/E2 |
| **API-Health-Checker** | Pings all `/api/*` endpoints hourly → alerts if down | Uptime monitoring |
| **Secret-Scanner** | Scans repo for exposed API keys → rotates them | Security H2 |
| **Docker-Deploy-Bot** | One-command deploy to Oracle ARM via SSH | CI/CD automation |
| **LLM-Cost-Tracker** | Logs AI token usage per user → predicts monthly spend | Cost management |

### 📢 Marketing Team — Content & Growth Tools
| Tool | What It Does | Use Case |
|------|-------------|----------|
| **SEO-Post-Generator** | Takes a job photo → auto-generates SEO blog post with keywords | Content C2 |
| **Tradie-POV-Script-Gen** | Generates TikTok/Reels scripts from job success stories | Content M6 |
| **Review-Collector** | Auto-sends WhatsApp nudge after job completion → collects Google reviews | Growth |
| **Lead-Score-Predictor** | ML model predicts which leads convert → prioritises callbacks | Sales |
| **Competitor-Tracker** | Monitors ServiceM8/Tradify pricing changes → alerts on differences | Strategy |

### 💰 Finance Team — Compliance & Billing Tools
| Tool | What It Does | Use Case |
|------|-------------|----------|
| **Voice-Invoice-Builder** | Dictate line items → auto-generates ATO-compliant invoice (GST, ABN) | FC1 |
| **GST-Calculator** | Auto-calculates 10% GST on any quote → validates against BAS | Compliance |
| **Receipt-Ocr-Scanner** | Photo of receipt → extracts data → populates expense tracker | Bookkeeping |
| **Subscription-Churn-Alert** | Monitors Stripe failed payments → triggers WhatsApp recovery flow | Revenue |
| **Profit-Margin-Calculator** | Input job costs → outputs margin breakdown → recommends pricing | Unit economics |

---

**Document Owner:** Product Manager / Founder  
**Last Updated:** 2026-04-13  
**Next Review:** 2026-04-30 (post-sprint)