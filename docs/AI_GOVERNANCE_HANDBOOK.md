# AI Governance Handbook — BackPocket OS

**Owner:** Fractional CTO / Compliance Officer  
**Classification:** Internal — Mandatory Reading for All Contributors  
**Version:** 1.0  
**Date:** 2026-04-19  
**Review Cadence:** Every 90 days (next: 2026-07-18) — see `docs/reviews/ai-handbook-90day-review.ics`  
**Companion Docs:**  
- Risk register & APP mapping → `docs/business/COMPLIANCE_AND_RISK_ANALYSIS.md`  
- Auth ADR → `docs/adr/001-auth.md`  
- Code audit & hosting → `docs/business/Code_audit_and_hosting.md`

---

## 1. Purpose

This handbook governs how AI is designed, deployed, and monitored inside BackPocket OS. Every pull request that touches AI behaviour — prompts, model selection, inference pipelines, training data, or automation scope — **must** pass the PR checklist in §8 before merge.

---

## 2. Regulatory Landscape (Australia-First)

| Regulation | Applicability | Key Obligation | Our Status |
|-----------|---------------|----------------|------------|
| **Privacy Act 1988 (Cth) + APPs** | Direct — we collect PII | APP 6: use only for primary purpose; APP 8: cross-border disclosure rules | Mapped in COMPLIANCE doc §3.3; implementation gaps remain (see §9) |
| **ATO e-invoicing (GST Act s29-70)** | Direct — we generate quotes/invoices | Tax invoice fields, 5-year retention, Peppol roadmap | Template enforced in `services/construction.py` |
| **Notifiable Data Breaches (NDB)** | Direct | 30-day OAIC notification on eligible breach | IR plan exists (COMPLIANCE doc §6); tooling gaps (no Sentry/alerting) |
| **OAIC Guidance on Generative AI (2024)** | Voluntary but expected | Transparency, human oversight, bias testing, purpose limitation | HITL implemented; transparency + bias testing gaps |
| **DISR Voluntary AI Safety Standard (2024)** | Voluntary — signals maturity to enterprise buyers | 10 guardrails including testing, transparency, accountability | Partially met (see §3 mapping) |
| **EU AI Act** | Defensive posture — not marketing to EU | Risk classification; high-risk AI system obligations | Geo-IP gate planned; not yet implemented |
| **Consumer Data Right (CDR)** | Future — if we ingest Open Banking | Accreditation required | Out of scope Year 1 |

---

## 3. AI Ethics Principles

Eight principles govern all AI features in BackPocket. Derived from Australia's AI Ethics Framework + DISR Voluntary Standard.

### P1 — Human Agency and Oversight

**Rule:** No customer-facing artefact (email, quote, invoice, social post) is dispatched without explicit human approval.

**Implementation:**
- `pending_approvals` table — every AI draft lands here first
- Dashboard: Approve / Revise / Discard — three explicit actions
- `audit_log` + `action_history` — immutable record of every decision
- Voice commands require confirmation gate before executing state changes

**Enforcement:** Architectural — there is no code path that bypasses the approval screen.

### P2 — Transparency and Explainability

**Rule:** Users must know when they are interacting with AI-generated content, and AI must not impersonate a human.

**Implementation:**
- Non-reliance disclaimer: *"Pip's suggestions are drafts. You're the tradie; you sign off."*
- AI-generated drafts are visually distinct in the UI (labelled as Pip's work)
- Confidence scores surfaced where available
- **GAP:** No model attribution shown to end user (which model generated this draft)

### P3 — Fairness and Non-Discrimination

**Rule:** AI must not discriminate based on protected attributes (race, gender, disability, location, etc.) when processing leads, generating quotes, or prioritising work.

**Implementation:**
- Quote pricing is formula-based (materials + labor × markup) — not AI-determined
- Lead urgency scoring uses explicit criteria (budget, timeline, job complexity) — not demographic proxies
- **GAP:** No formal bias testing or audit of AI outputs against protected attributes

### P4 — Privacy Protection and Data Governance

**Rule:** Minimise data collection. Keep PII local. Redact before cloud calls.

**Implementation:**
- Local-first architecture: Ollama → OpenRouter fallback (3-tier in `services/gemini.py`)
- `LOCAL_AI_ONLY=1` env var allows full cloud opt-out
- **CRITICAL GAP:** PII redaction before OpenRouter calls is **not implemented**. Compliance doc §3.3 APP 8 claims it exists — it does not. Raw email content (names, emails, phone numbers, addresses) is sent to OpenRouter when local AI is unavailable.

**Required Action:** Implement `_redact_pii(text)` function before all cloud AI calls. Priority: HIGH.

### P5 — Reliability and Safety

**Rule:** AI failures must degrade gracefully. Bad outputs must not reach customers.

**Implementation:**
- 3-tier AI fallback: Local → Ollama → OpenRouter → Gemini (`services/gemini.py`)
- HITL prevents bad outputs from reaching customers
- Price delta flagging: quote >20% outside historical median → red warning
- **GAP:** No automated output validation (schema checks on AI JSON responses are partial)

### P6 — Accountability

**Rule:** Every AI decision must be traceable to a human who approved it.

**Implementation:**
- `audit_log` table: action, details, timestamp for every state change
- `corrections` table: tracks when user overrides AI suggestion
- `action_history`: full decision chain from email → draft → approval
- **GAP:** No formal accountability officer assigned; sign-offs in COMPLIANCE doc are all `_pending_`

### P7 — Contestability

**Rule:** Users can challenge and correct any AI output.

**Implementation:**
- Revise action on every pending approval
- Corrections feed back into RAG (ChromaDB) for continuous improvement
- APP 13 (Correction) supported via editable fields
- **GAP:** No formal complaints/escalation process documented

### P8 — Continuous Improvement

**Rule:** AI must learn from corrections and improve over time.

**Implementation:**
- Agentic RAG pipeline: triage → approve/revise → ingest to ChromaDB
- `learned_patterns` table: pattern_type, confidence_score, usage_count
- `session_memory`: per-session context accumulation
- 62 seed documents in vector DB (admin: 55, accountant: 18, auditor: 4)
- **GAP:** No metrics dashboard tracking improvement over time (accuracy, correction rate)

---

## 4. Project Rules — Never / Always / Grey Zone

### NEVER

| # | Rule | Reason |
|---|------|--------|
| N1 | Never auto-send any customer-facing content | HITL is our primary compliance control |
| N2 | Never store API keys in code or commits | Use `.env` + secrets manager |
| N3 | Never train on customer data without explicit opt-in | APP 6 — purpose limitation |
| N4 | Never let AI set final prices | Formula-based pricing; AI suggests, human approves |
| N5 | Never log full OAuth tokens in application logs | Token leakage risk |
| N6 | Never send PII to cloud AI without redaction | APP 8 — cross-border disclosure (currently violated — see §3 P4) |
| N7 | Never bypass the confirmation gate in voice commands | Prevents accidental state mutations |

### ALWAYS

| # | Rule | Reason |
|---|------|--------|
| A1 | Always route AI drafts through `pending_approvals` | Architectural HITL |
| A2 | Always log AI interactions to `audit_log` | Traceability for ATO/OAIC |
| A3 | Always try local AI before cloud fallback | Privacy + cost optimisation |
| A4 | Always include non-reliance disclaimer on AI outputs | Legal liability shield |
| A5 | Always validate AI JSON output against expected schema | Prevent hallucinated fields from propagating |
| A6 | Always ingest corrections into RAG | Continuous improvement flywheel |

### GREY ZONE — Requires Team Discussion

| Scenario | Consideration |
|----------|--------------|
| Auto-categorising leads without approval | Low risk (internal only) but sets precedent for automation creep |
| Using AI confidence scores to auto-prioritise inbox | Acceptable if user can override; document the threshold |
| Caching AI responses for repeated queries | Performance win but stale data risk; TTL must be short |
| Expanding RAG training to include client emails | Privacy implications; needs explicit consent mechanism |

---

## 5. Four Mental Models

Use these lenses when making AI decisions. If any lens raises a flag, stop and discuss.

### 🔍 The Regulator Test
> *"If the OAIC or ATO reviewed this feature tomorrow, would we be comfortable explaining how it works, what data it touches, and what controls exist?"*

### 👷 The Steve Test
> *"Would Steve (our prototype tradie user) understand what Pip did, why, and how to override it? Would he trust it with his business?"*

### 📰 The Front-Page Test
> *"If this AI behaviour appeared in a news article — 'Tradie app sends wrong quote / leaks customer data / discriminates against suburb' — would we be embarrassed?"*

### 🤝 The Trust Test
> *"Does this feature build trust with the user, or does it feel like the AI is making decisions behind their back?"*

---

## 6. AI Feature Inventory

Current AI-powered features and their risk classification.

| Feature | Description | Risk Level | HITL? | Data Sent to Cloud? |
|---------|-------------|-----------|-------|---------------------|
| Email draft generation | Pip drafts email responses | Medium | ✅ Yes | Yes — full email body (PII gap) |
| Lead extraction from email | AI parses email → structured lead | Medium | ✅ Yes (user reviews lead) | Yes — full email body |
| Tradie follow-up messages | AI generates friendly follow-up | Low | ✅ Yes (draft only) | Yes — quote details |
| Quote price suggestions | AI suggests based on job patterns | Medium | ✅ Yes (human sets final price) | Yes — job description |
| Voice intent classification | 46-intent taxonomy | Low | Partial (confirmation gate) | No — local classifier first |
| Entity extraction (voice) | Fuzzy matching names, jobs, locations | Low | ✅ Yes (confirmation) | No — local processing |
| Document/invoice analysis | Vision API for uploaded images | Medium | ✅ Yes (user reviews) | Yes — image content |
| Communication coach | GPT-4o reviews drafts for tone | Low | ✅ Yes (advisory only) | Yes — draft text |
| RAG retrieval | Semantic search over past decisions | Low | No (internal context only) | No — ChromaDB local |

---

## 7. Data Flow — AI Pipeline

```
┌─────────────────────────────────────────────────────┐
│                   INBOUND DATA                       │
│  Email body, voice transcript, uploaded document     │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  STEP 1: Sensitivity Classification                  │
│  ┌─────────────────────────────────────────────┐     │
│  │ _classify_sensitivity(text)                 │     │
│  │ High entropy (> 4.0) → cloud AI             │     │
│  │ Low entropy → local AI sufficient           │     │
│  └─────────────────────────────────────────────┘     │
│  ⚠️  GAP: No PII redaction step here                 │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  STEP 2: AI Inference (3-tier fallback)              │
│  1. Local AI server (private) ──────── if available  │
│  2. OpenRouter (cloud) ─────────────── fallback      │
│  3. Gemini native (cloud) ──────────── last resort   │
│                                                      │
│  RAG context injected from ChromaDB before inference │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  STEP 3: Output Handling                             │
│  - Parse AI response (JSON or text)                  │
│  - Store in pending_approvals                        │
│  - Log to audit_log                                  │
│  - Surface to user in dashboard / mobile app         │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  STEP 4: Human-in-the-Loop                           │
│  ┌────────────┬──────────────┬───────────────┐       │
│  │  APPROVE   │   REVISE     │   DISCARD     │       │
│  │  & Send    │   (correct)  │   (reject)    │       │
│  └─────┬──────┴──────┬───────┴───────┬───────┘       │
│        │             │               │               │
│        ▼             ▼               ▼               │
│   Execute action  Ingest to RAG  Log rejection       │
│   Log to audit    as correction  Log to audit        │
└──────────────────────────────────────────────────────┘
```

---

## 8. PR Checklist — AI-Touching Changes

**Every PR that modifies prompts, model config, inference pipelines, AI data flows, or automation scope MUST complete this checklist.**

Copy into your PR description:

```markdown
### AI Governance Checklist

- [ ] **HITL preserved**: No new code path bypasses `pending_approvals`
- [ ] **Prompt reviewed**: New/modified prompts checked for bias, hallucination risk, prompt injection vectors
- [ ] **Data flow documented**: What data is sent to which AI provider? PII implications noted
- [ ] **Local-first respected**: Cloud AI is fallback only; `LOCAL_AI_ONLY=1` still works
- [ ] **Non-reliance disclaimer**: AI outputs include appropriate disclaimers
- [ ] **Audit trail**: All AI decisions logged to `audit_log` or `action_history`
- [ ] **RAG impact**: If changing prompts/models, existing RAG corrections still apply correctly
- [ ] **Schema validation**: AI JSON output validated against expected Pydantic model
- [ ] **Rollback plan**: Can this change be reverted without data loss?
- [ ] **Mental model check**: Passes Regulator / Steve / Front-Page / Trust tests (§5)
- [ ] **No new PII to cloud**: If sending new data fields to cloud AI, document and get approval
- [ ] **Voice safety**: If touching voice pipeline, confirmation gate still enforced
```

---

## 9. Known Compliance Gaps (Action Register)

| # | Gap | Severity | Principle | Required Action | Target Date |
|---|-----|----------|-----------|-----------------|-------------|
| G1 | **PII not redacted before cloud AI calls** | CRITICAL | P4 | Implement `_redact_pii()` in `services/gemini.py` before `get_openrouter_response()` and `_draft_response_openrouter()` | Sprint Day 8 |
| G2 | **No `/privacy` route or privacy policy page** | CRITICAL | P2 | Create privacy policy + serve at `/privacy` endpoint | Sprint Day 9 |
| G3 | **No consent collection on first run** | HIGH | P2, P4 | Add in-app consent flow (APP 5 notification) | Sprint Day 10 |
| G4 | **No bias testing framework** | HIGH | P3 | Define test cases for lead scoring + quote generation across demographics | Sprint Day 12 |
| G5 | **No model attribution in UI** | MEDIUM | P2 | Show which AI model generated each draft | Sprint Day 11 |
| G6 | **Compliance sign-offs pending** | HIGH | P6 | Get CTO + Compliance Officer signatures on COMPLIANCE doc | Sprint Day 8 |
| G7 | **No Sentry / alerting for IR plan** | HIGH | P5 | Deploy Sentry; connect to IR runbook triggers | Sprint Day 10 |
| G8 | **ChromaDB not persistent across redeploys** | MEDIUM | P8 | Migrate to persistent vector store or add volume mount | Sprint Day 12 |
| G9 | **No formal complaints/escalation process** | MEDIUM | P7 | Document escalation path for AI disputes | Sprint Day 11 |
| G10 | **OAuth tokens stored as plaintext JSON** | HIGH | P4 | Encrypt with Fernet + per-user key; move to DB | Epic F |

---

## 10. Incident Response — AI-Specific

In addition to the general IR plan (COMPLIANCE doc §6), AI-specific incidents require:

### AI Hallucination Incident
1. **Detect**: User reports incorrect quote/email/invoice content
2. **Contain**: Flag the specific `pending_approval` or `audit_log` entry
3. **Assess**: Was the hallucination caught by HITL? Did it reach a customer?
4. **Remediate**: Add correction to RAG; review prompt for root cause; update `learned_patterns`
5. **Prevent**: If pattern is systemic, add output validation rule

### AI Data Leak Incident
1. **Detect**: Discovery that PII was sent to cloud AI without consent/redaction
2. **Contain**: Switch to `LOCAL_AI_ONLY=1` immediately
3. **Assess**: What PII was exposed? Which cloud provider? Retention policy of provider?
4. **Notify**: If "eligible data breach" threshold met → OAIC within 30 days
5. **Remediate**: Implement PII redaction (Gap G1); audit all cloud AI call sites

### Prompt Injection Incident
1. **Detect**: AI produces unexpected output from email/document input
2. **Contain**: Quarantine the input; review `pending_approvals` for tainted drafts
3. **Assess**: Was the injection successful? Did it bypass HITL?
4. **Remediate**: Strengthen input sanitisation; add delimiter hardening to prompts

---

## 11. Roles and Responsibilities

| Role | Responsibility | Current Holder |
|------|---------------|----------------|
| **AI Ethics Lead** | Owns this handbook; reviews AI PRs against checklist | _To be assigned_ |
| **Compliance Officer** | Signs off on regulatory mapping; owns IR plan | _To be assigned_ |
| **CTO** | Architectural decisions; gap remediation prioritisation | Founder (interim) |
| **All Contributors** | Follow PR checklist; raise concerns via grey-zone process | Everyone |

---

## 12. Review and Amendment

- This handbook is reviewed every **90 days** (calendar invite: `docs/reviews/ai-handbook-90day-review.ics`)
- Any material change to AI features triggers an ad-hoc review
- Amendments require sign-off from AI Ethics Lead + CTO
- Version history maintained in git

| Version | Date | Change | Author |
|---------|------|--------|--------|
| 1.0 | 2026-04-19 | Initial creation — 8 principles, PR checklist, gap register, incident response | Team |

---

**This document is mandatory reading for all contributors working on AI features.**  
**If in doubt, apply the four mental models (§5). If still in doubt, ask.**
