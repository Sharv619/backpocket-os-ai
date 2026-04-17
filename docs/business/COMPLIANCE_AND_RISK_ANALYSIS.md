# Compliance & Risk Analysis

**Owner:** Compliance Officer / Fractional CTO / Legal Counsel  
**Audience:** Enterprise buyers, investor due diligence, ATO / OAIC review  
**Classification:** Internal — Pre-Launch  
**Date:** 2026-04-13  
**Review Cadence:** Quarterly, or on any material system change

---

## 1. Executive Summary

BackPocket operates as a **System of Record (SoR) with a local-first data residency posture**, differentiating materially from cloud-native SaaS competitors whose data architectures externalise the customer's operational truth. This document enumerates our regulatory obligations under Australian Taxation Office (ATO) e-invoicing standards, the Privacy Act 1988 (Cth) and the Australian Privacy Principles (APPs), the EU General Data Protection Regulation (GDPR) for any inbound EU data subjects, and our technical risk register with codified mitigations.

**Key Position:** Our local-first architecture is not incidental — it is a deliberate compliance moat. Customer PII and financial records are stored on infrastructure the customer controls (on-device or self-hosted), reducing our data-controller liability surface and providing a durable competitive advantage over pure-cloud SaaS vendors.

---

## 2. ATO Compliance — Invoice & Financial Records

### 2.1 Applicable Obligations

| Obligation | Source | Requirement | Our Control |
|-----------|--------|------------|-------------|
| **Tax invoice fields** | A New Tax System (GST) Act 1999 s29-70 | ABN, supplier name, date, description, GST amount, total | Template enforced in `services/construction.py`; rendered invoice validated before dispatch |
| **Record retention** | ITAA 1997 s262A | **5 years** minimum from date of transaction or until any dispute is resolved | Postgres row-level retention policy; immutable `audit_log` table; exportable archive bundle |
| **E-invoicing (Peppol)** | ATO Peppol Authority framework | UBL 2.1 XML format; PINT A-NZ specification | Roadmap Epic (Q3): integrate with Peppol Access Point provider (e.g., MessageXchange, Ozedi) |
| **GST reporting alignment** | BAS lodgement obligations | Outputs must reconcile to BAS line items | `quotes` and `payments` tables map 1:1 to BAS categories; export to accounting packages (Xero, MYOB) |
| **Electronic record integrity** | TR 2018/2 (Electronic Record-Keeping) | Records must be complete, accurate, and accessible in English for the retention period | WAL-journaled Postgres; Cloudflare R2 cold-storage backup; tamper-evident hash chain on `audit_log` |

### 2.2 Invoice Generation Pipeline — Compliance Checkpoints
### 2.3 Attestation

-   We are not a **registered tax agent** under the Tax Agent Services Act 2009; our Terms of Service explicitly disclaim tax advice and direct customers to a registered agent for BAS/GST lodgement.
-   AI-generated content includes a **non-reliance clause** in the user interface: *"Pip's suggestions are drafts. You're the tradie; you sign off."*

---

## 3. Privacy — APP, GDPR, and the Local-First Moat

### 3.1 Regulatory Surface

| Framework | Jurisdiction | Our Exposure | Classification |
|-----------|--------------|-------------|----------------|
| **Privacy Act 1988 (Cth) / APPs** | Australia (primary) | Direct — we collect PII (names, emails, phone, financial records) | **APP Entity** (once revenue >$3M, mandatory regardless for health/credit info) |
| **Notifiable Data Breaches scheme (NDB)** | Australia | Mandatory notification to OAIC + affected individuals within 30 days of reasonable belief of "eligible data breach" | Incident Response Plan (§6.2) |
| **GDPR** | EU / EEA | Indirect — applies if we offer services to EU data subjects or monitor their behaviour. We do not currently market to EU. | Defensive posture; gated geo-IP at signup to prevent inadvertent exposure |
| **Consumer Data Right (CDR)** | Australia | Future-state — relevant if we ingest Open Banking data for payment reconciliation | Out of scope for Year 1 |

### 3.2 The Local-First Privacy Moat

Our architecture is fundamentally different from competitor SaaS offerings:

| Dimension | Typical SaaS Competitor | BackPocket |
|-----------|-------------------------|-----------|
| **Primary data location** | Vendor's cloud (AWS/GCP) | Customer's device or self-hosted Oracle instance |
| **AI inference location** | Third-party API (OpenAI, Anthropic) — data leaves jurisdiction | **Ollama local-first**; OpenRouter only as fallback, with PII redaction |
| **Data controller posture** | Vendor is joint controller; complex DPA required | Customer is sole controller for local data; BackPocket is processor only for opt-in cloud features |
| **Cross-border transfer exposure** | High — APP 8 obligations trigger on every request | Minimal — inference stays on-shore / on-device |
| **Breach blast radius** | Multi-tenant breach = all customers | Per-customer isolation; single compromise = single customer |

**This is a defensible enterprise-sales claim.** It materially simplifies procurement with risk-averse buyers (builders, councils, government subcontractors).

### 3.3 APP-by-APP Mapping

| APP | Principle | Our Implementation |
|-----|-----------|--------------------|
| **APP 1** — Open and transparent management | Privacy Policy published at `/privacy`; clear plain-English summary |
| **APP 3** — Collection of solicited info | Data minimisation: we collect only lead/quote/job fields necessary for the service |
| **APP 5** — Notification of collection | In-app notice on first run + email confirmation |
| **APP 6** — Use or disclosure | Data used only for the primary purpose; no secondary sale; AI training on customer data is **opt-in and per-tenant only** |
| **APP 8** — Cross-border disclosure | OpenRouter fallback disclosed; PII redaction before cloud call; user can disable via `LOCAL_AI_ONLY=1` |
| **APP 11** — Security of personal info | Encryption at rest (Postgres TDE), TLS 1.3 in transit, per-user encrypted OAuth tokens |
| **APP 12** — Access | Self-service export (JSON bundle) from dashboard |
| **APP 13** — Correction | Customer can edit/delete any field; corrections logged to `corrections` table |

### 3.4 GDPR Defensive Posture

-   **Lawful basis**: Contract performance (Art. 6(1)(b)) for core service; Consent (Art. 6(1)(a)) for marketing.
-   **Data Subject Rights**: Access, rectification, erasure, portability — all supported by the export + delete endpoints.
-   **DPO**: Not mandatory (we are not public authority, large-scale monitoring, or special category data at scale). Compliance owner assigned as interim.
-   **Transfer mechanism**: Standard Contractual Clauses (SCCs) with OpenRouter; Data Processing Addendum executed.

---

## 4. Risk Register

Risks are rated on a 5×5 matrix (Likelihood × Impact). Top-tier risks are documented here; full register is maintained in `/docs/risk/REGISTER.xlsx`.

### 4.1 Technical Risks

| ID | Risk | L | I | Score | Mitigation | Owner |
|----|------|---|---|-------|-----------|-------|
| **T-01** | **AI hallucination in generated quotes/invoices** (e.g., wrong GST, fabricated line items) | 4 | 5 | **20** | **Human-in-the-loop approval screen is mandatory and non-skippable.** No quote or invoice is sent without an explicit user-approval action. UI surfaces AI confidence score. Disclaimer in product copy. | CTO |
| **T-02** | **AI hallucination in tradie follow-up messages** (tone misalignment, factual error) | 3 | 3 | 9 | Draft-only generation; user reviews every message in the Peace of Mind Inbox before dispatch. Corrections feed RAG for continuous improvement. | PM |
| **T-03** | **SQLite concurrency ceiling at scale** | 5 | 4 | **20** | Migrate to Postgres (WBS Epic A). Interim: per-user SQLite files with connection pooling. | CTO |
| **T-04** | **OAuth token compromise** (token.json on disk) | 2 | 5 | 10 | Encrypt tokens at rest (Fernet, per-user key). Move to Postgres `user_credentials` table with KMS-backed encryption. | CTO |
| **T-05** | **Dependency on third-party AI (OpenRouter outage)** | 3 | 2 | 6 | 3-tier fallback already implemented (`services/gemini.py`): Local AI → Ollama → OpenRouter → Gemini. Graceful degradation verified. | CTO |
| **T-06** | **Data loss during migration (SQLite → Postgres)** | 2 | 5 | 10 | Dual-write period (2 weeks); read-verification; rollback plan; backup snapshots every 6hrs during migration. | CTO |
| **T-07** | **Mobile device loss with local data** | 3 | 4 | 12 | Device PIN + biometric required; encrypted SQLite on-device; cloud sync as opt-in backup. | CTO |
| **T-08** | **Prompt injection via email content** | 3 | 3 | 9 | Structured prompt templates; email body is quoted/delimited; output schema validation (Pydantic). | CTO |

### 4.2 Business / Regulatory Risks

| ID | Risk | L | I | Score | Mitigation | Owner |
|----|------|---|---|-------|-----------|-------|
| **B-01** | **ATO determines our invoices are non-compliant** | 2 | 5 | 10 | Invoice template reviewed by external tax counsel pre-launch. Peppol roadmap (Q3). Non-reliance disclaimer. | Compliance |
| **B-02** | **OAIC Notifiable Data Breach** | 2 | 5 | 10 | IR plan (§6.2); breach drill quarterly; cyber insurance bound pre-launch. | Compliance |
| **B-03** | **Competitor (ServiceM8) launches equivalent AI** | 4 | 3 | 12 | Local-first moat + Pip brand + Western Sydney distribution lock-in. 18-month window to category-lead. | Founder |
| **B-04** | **Pricing resistance ($299 upfront)** | 3 | 3 | 9 | Founder pricing ($199) for first 100 to de-risk; financing option at $25/mo for 12 months. | PM |
| **B-05** | **Reliance on a single founder ("Steve the prototype user")** | 3 | 3 | 9 | Pioneer programme (10 design partners) diversifies feedback signal. | PM |
| **B-06** | **Google API ToS change (Gmail / Drive)** | 2 | 4 | 8 | Workspace Marketplace listing + OAuth review completed. Fallback: IMAP/SMTP path exists (`services/imap.py`). | CTO |

### 4.3 Top-3 Focus Risks — Deep Controls

**T-01 — AI hallucination in quotes**
-   **Primary control**: Human-in-the-loop mandatory approval (no auto-send).
-   **Secondary control**: Price delta flagging — if generated quote is >20% outside historical median for job type, UI shows a red warning.
-   **Tertiary control**: All AI outputs logged to `corrections` table; any customer-reported error triggers a root-cause review and updates the prompt template.
-   **Residual risk**: Low — human is in the loop by architectural design, not by policy.

**T-03 — SQLite concurrency**
-   **Primary control**: Postgres migration is Epic A, Week 3 (see WBS).
-   **Secondary control**: Per-user SQLite sharding as interim for pilot.
-   **Residual risk**: Medium until migration complete. Pilot is capped at 10 design partners to stay within single-writer envelope.

**B-02 — Notifiable Data Breach**
-   **Primary control**: Encryption at rest + in transit; least-privilege IAM on Oracle VM; Cloudflare zero-trust ingress.
-   **Secondary control**: 24-hour IR runbook; OAIC notification template drafted and counsel-reviewed.
-   **Tertiary control**: Cyber liability insurance ($2M cover, bound at Pilot launch).
-   **Residual risk**: Low — the local-first architecture means any breach is per-customer, not systemic.

---

## 5. Human-in-the-Loop (HITL) Governance

The HITL control is the single most important mitigation in this document. It is documented here for audit purposes.

**Principle:** *No customer-facing artefact — email, quote, invoice, social post — is dispatched by AI autonomously. A human (Steve) approves every outbound action.*

**Implementation:**
-   `pending_approvals` table — every AI draft lands here first.
-   Dashboard UI — Steve sees sender, subject, draft, confidence indicators, suggested actions.
-   Three explicit actions: **Approve & Send**, **Revise**, **Discard**.
-   `action_history` + `audit_log` — every decision is immutably logged with timestamp and ref_id.

**This is both a compliance control and a product feature.** It also is the training data moat: every correction improves Pip.

---

## 6. Incident Response

### 6.1 Severity Tiers

| Tier | Definition | Response SLA |
|------|-----------|-------------|
| **SEV-1** | Suspected PII breach; financial data exposure | 1 hour detect → triage; 4 hour containment; 30-day OAIC notification window |
| **SEV-2** | Production outage; AI pipeline down | 1 hour detect; 4 hour restoration |
| **SEV-3** | Degraded feature; single-customer issue | 1 business day |
f
### 6.2 SEV-1 Runbook (Summary)

1.  Detect → alert on-call via Sentry / UptimeRobot.
2.  Contain → isolate affected instance; rotate credentials.
3.  Assess → determine "eligible data breach" threshold (NDB scheme).
4.  Notify → OAIC + affected individuals within 30 days.
5.  Remediate → root-cause analysis; control uplift; post-mortem filed.

### 6.3 Dependencies

-   Cyber insurance: policy + insurer contact in `/docs/compliance/insurance.md`
-   Legal counsel on retainer pre-launch
-   OAIC notification template drafted

---

## 7. Accepted Risks

| Risk | Why Accepted | Review Trigger |
|------|-------------|----------------|
| GDPR direct applicability | We do not market to EU; gated geo-IP at signup | If we launch in EU |
| ISO 27001 / SOC 2 certification | Cost/value not justified pre-$1M ARR | At $1M ARR or first enterprise buyer RFP |
| CDR (Open Banking) accreditation | Out of Year 1 scope | If we add payment reconciliation via bank feeds |

---

**Sign-off**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Compliance Officer | _pending_ | | |
| CTO | _pending_ | | |
| Legal Counsel | _external retainer_ | | |