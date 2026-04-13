# AI Governance Handbook — Dev Edition

**For:** The solo dev / founder building BackPocket  
**Purpose:** What rules apply to you, what ethics demand of you, and what to do *before* you ship an AI feature  
**Read time:** 15 minutes  
**Re-read:** Every new AI feature, every 90 days, or when a big regulation lands

---

## 0. Why This Document Exists

You are shipping an AI product that:
-   Touches PII (names, emails, phone numbers)
-   Generates financial documents (quotes, invoices) that the ATO cares about
-   Writes on behalf of a human (Steve) to his customers
-   Learns from his corrections

That puts you in a regulated zone whether you like it or not. This handbook is your **pre-flight checklist** so you don't crash into a rule you didn't know existed.

**Ethics isn't a PR exercise.** For this product, it's the moat. Competitors can copy features. They can't easily copy the trust that comes from a local-first, human-in-the-loop, transparent system.

---

## 1. The Changing Landscape (2024 → 2026 → beyond)

### What's already landed

| Jurisdiction | Framework | Status | What It Means For You |
|--------------|-----------|--------|----------------------|
| **🇦🇺 Australia** | Australia's AI Ethics Principles (8 principles, voluntary) | Live since 2019 | Voluntary, but regulators treat it as the reasonableness baseline |
| **🇦🇺 Australia** | Privacy Act 1988 + APPs | Live | **Hard law.** Governs every bit of PII you touch |
| **🇦🇺 Australia** | Proposed Privacy Act reforms (tiered penalties, automated-decision rights) | Bills moving through Parliament 2025–26 | New "right to meaningful information about automated decisions" — plan for it |
| **🇦🇺 Australia** | Voluntary AI Safety Standard (DISR, Sept 2024) | Live (voluntary) | 10 guardrails; treat as best-practice playbook |
| **🇦🇺 Australia** | Mandatory guardrails for high-risk AI (proposed) | Consultation closed; legislation pending | Might reach "high-risk" if we touch credit/health decisions — we currently don't |
| **🇪🇺 EU** | EU AI Act | Phased 2024–2027. Prohibitions from Feb 2025. GPAI rules Aug 2025. High-risk from 2026 | Only applies if we sell to EU or affect EU subjects — **we don't, and we gate it** |
| **🇺🇸 US** | Colorado AI Act, NY RMF, state-by-state patchwork | Rolling 2024–2026 | Not selling in US yet; irrelevant for now |
| **🌍 Global** | NIST AI RMF 1.0, ISO/IEC 42001, ISO/IEC 23894 | Live standards | Great voluntary reference; map to later for enterprise sales |

### What's coming (watch list)

-   **AU Privacy Act Tranche 2 reforms** — expect statutory tort for serious privacy invasions, fair-and-reasonable test on collection, and meaningful transparency on automated decisions.
-   **AU mandatory AI guardrails** for "high-risk" settings — if triggered, requires risk management, HITL, disclosure, records.
-   **EU AI Act GPAI obligations** (Aug 2025) — if you ever ship in EU, upstream model providers (Gemini, Llama) must disclose training data; you inherit downstream duties.
-   **Australian Consumer Law + misleading AI outputs** — the ACCC has signalled that AI-generated claims must not mislead. Bad quote = potentially a consumer-law breach.

### Signal for BackPocket

-   **Not currently a "high-risk AI" product** under any framework (we're not credit scoring, hiring, health diagnosis, or law enforcement).
-   **We are a data processor handling PII + financial docs** — so the Privacy Act + ATO obligations bite regardless of AI framing.
-   **Our local-first architecture defuses most of the new regs.** Most AI regulation is about "don't surveil, don't automate-decide without oversight, don't leak data" — we don't, because our design doesn't.

---

## 2. The Rules That Apply To BackPocket *Today*

Ranked by "things that bite first".

### 2.1 Privacy Act 1988 + APPs (Australia) — **HARD LAW**

Applies the moment we hit $3M revenue or handle health/credit data. We're under that threshold now, but **build as if it already applies** — you won't have time to retrofit.

**What you must do:**
-   APP 1: Publish a privacy policy at `/privacy` (drafted, ship with Epic H)
-   APP 3: Collect only what's necessary — minimise fields
-   APP 5: Notify users at collection what data and why
-   APP 6: Don't use data for anything not disclosed
-   APP 8: **Disclose cross-border disclosure** (OpenRouter = US, Gemini = US) — this one catches people
-   APP 11: Encrypt at rest + in transit. Tokens = Fernet-encrypted per user.
-   APP 12/13: Self-serve export + delete

**Notifiable Data Breaches (NDB) scheme:** if an "eligible data breach" happens, you have **30 days** to notify OAIC + affected users. Have the template drafted *before* you need it.

### 2.2 ATO — Invoice Compliance

-   Tax invoice fields (GST Act s29-70): ABN, date, supplier, GST amount, total, description
-   5-year retention (ITAA 1997 s262A)
-   Non-reliance disclaimer in UI: *"Pip's suggestions are drafts. You're the tradie; you sign off."*
-   Not a registered tax agent (Tax Agent Services Act 2009) — don't give tax advice

### 2.3 Australian Consumer Law (ACL)

-   Services must be supplied with due care and skill. If AI-generated content misleads the customer, **we are liable**, not the model vendor.
-   Pricing/quotes must not be misleading. Disclosure that quotes are AI-assisted + human-reviewed = safer.

### 2.4 OAIC Voluntary Guidance on Generative AI (2024)

Not law, but the OAIC has published specific guidance:
-   Be transparent that PII goes into AI
-   Assess necessity before using AI for a given task
-   Don't use external AI for sensitive data without additional safeguards
-   Secondary use of training data needs a fresh lawful basis

### 2.5 Intellectual Property

-   **Model outputs**: not clearly copyrightable in AU; treat as public-domain-ish. Don't build moat assumptions on "our AI-generated copy is ours".
-   **Training on customer data**: our policy = **opt-in, per-tenant only**. Default off. Put this in the privacy policy.
-   **Third-party model T&Cs**: OpenRouter, Gemini — each has its own use/redistribution rules. Read them. Especially: *don't* train a competing model on their outputs (OpenAI bans this explicitly).

---

## 3. The 8 Ethical Principles — Applied to BackPocket

Australia's AI Ethics Principles are the local benchmark. Here's what each one demands of you in *this codebase*:

| Principle | What It Means | How We Implement |
|-----------|---------------|-----------------|
| **Human, social & environmental wellbeing** | AI should benefit people | We sell 13 hrs/week back. Measurable wellbeing outcome. |
| **Human-centred values** | Respect autonomy, dignity | We automate drudgery, not judgement. Steve still signs every email. |
| **Fairness** | No discrimination | We don't score, rank, or exclude users based on protected attributes. Period. |
| **Privacy protection & security** | Data respected | Local-first. Encrypted at rest. Per-tenant isolation. Fernet tokens. |
| **Reliability & safety** | Works as intended | 3-tier AI fallback. HITL gate. Graceful degradation when APIs fail. |
| **Transparency & explainability** | Users know when/how AI is used | Pip is clearly branded. Every draft is marked AI-generated. Confidence scores in UI. |
| **Contestability** | Users can challenge decisions | Every draft is editable before send. `corrections` table feeds back into Pip. |
| **Accountability** | Someone is responsible | `audit_log` table logs every AI action. Founder signs off. Not "the model did it". |

**If you ever catch yourself rationalising "the AI made the decision, not me" — stop. That's the accountability principle failing. You're responsible.**

---

## 4. Project-Specific Ethical Lines

These are rules *we* set, not regulation. Hold them even when it's inconvenient.

### Never

-   **Never auto-send AI-generated communications.** Human approval is architectural, not configurable. No "auto-approve after X hours" flag. Full stop.
-   **Never train on customer data without explicit per-tenant opt-in.** Default is off. Not buried in TOS — a clear UI toggle.
-   **Never present AI output as certainty.** Use confidence scores, "Pip thinks...", "draft for your review". Language matters.
-   **Never send customer PII to a cloud model if a local model can do the job.** Ollama first, cloud second.
-   **Never use dark patterns** to increase engagement (streaks, FOMO, etc.). We sell back time, not steal it.
-   **Never scrape/ingest competitor data** to build our RAG. Our moat is real corrections, not pilfered knowledge.

### Always

-   **Always log the AI action.** Every draft, every triage decision, every voice→quote → `audit_log`.
-   **Always show the draft before send.** Pending approvals are the product's soul.
-   **Always let the user delete everything.** Right to erasure is non-negotiable.
-   **Always disclose cross-border transfer.** OpenRouter is US. Gemini is US. Say so.
-   **Always make the fallback path work without AI.** Steve should be able to run his business if every AI provider goes dark.

### Grey Zones — Think Before You Ship

-   **Using customer quotes to tune prompts** — OK if anonymised, opt-in, disclosed.
-   **A/B testing AI models on live users** — OK if both models produce reviewed drafts (HITL protects).
-   **Sending aggregate usage metrics to Sentry/analytics** — OK; it's not PII if anonymised. Never send email bodies or quote contents.
-   **Storing voice recordings** — only with consent, only as long as needed for transcription (then delete the audio; keep the transcript).

---

## 5. The Dev Checklist — Before You Merge an AI Feature

Copy this into every PR description that touches AI:
AI Feature Checklist

Data flow

    What PII does this feature touch?

    Does it leave the device / our server?

    Is the user told (at collection) that AI will see this?

HITL

    Is there a human-approved step before any outbound action?

    Can the user edit the AI output before it's used?

    Is the output marked as AI-generated in the UI?

Fallback

    What happens if Ollama is down?

    What happens if OpenRouter is down?

    What happens if both are down?

    Does the app show a graceful message, not a crash?

Audit

    Is this action logged to audit_log?

    Is the draft persisted so the user can review/dispute later?

    Is the prompt template versioned (so we can diff "what Pip thought then")?

Opt-out

    Can the user turn this feature off entirely?

    If using customer data for model improvement, is it opt-in?

Compliance

    Does this store/transmit data cross-border? If so, is it disclosed?

    Does the output claim anything that must be accurate (prices, legal, tax)? If so, what's the disclaimer?

    If this generates an invoice/quote, does it meet ATO fields?

code Code

**If any box is blank, don't ship.** Ask "what would a regulator assume if I couldn't answer this?"

---

## 6. Red Flags — Things That Should Stop a Merge

-   Auto-send without human approval
-   Cloud API called without PII redaction
-   Logs that include email bodies, quote amounts with client names, or raw voice transcripts
-   Training loop that ingests customer data without an opt-in flag
-   A prompt template that says "pretend you are a lawyer/accountant/doctor"
-   Error handling that exposes API keys, stack traces, or customer data to the UI
-   Any feature that requires a user to trust the AI blindly (no edit step)
-   Any feature that collects data "just in case" without a stated purpose

If you see one of these in your own code, delete it. If you see one in a contractor's code, reject the PR.

---

## 7. When to Update This Handbook

Re-read and revise this doc when:

1.  **New feature involving AI** — before design, not after
2.  **Every 90 days** — calendar reminder
3.  **New customer segment** (e.g., we start selling to builders with employees = employment-law implications)
4.  **New geography** (US = state patchwork, UK = ICO, EU = AI Act triggers)
5.  **Any regulator publishes new guidance** — OAIC, ATO, ACCC, DISR
6.  **Any incident** — post-mortem should feed back into this doc
7.  **Any customer complaint about AI behaviour** — even if unfounded, log it and check the principle at stake

---

## 8. Learning Resources (Build Your Muscle)

Add these to a weekly 30-min reading habit. You don't need to be a lawyer; you need to smell a problem before it becomes one.

### Must-read, now

-   **OAIC guidance on AI and privacy** — https://www.oaic.gov.au (search "generative AI")
-   **Australia's AI Ethics Principles** — https://www.industry.gov.au/publications/australias-artificial-intelligence-ethics-principles
-   **Voluntary AI Safety Standard (DISR, Sept 2024)** — 10 guardrails; read the exec summary at minimum
-   **Privacy Act 1988 — APP quick reference** — OAIC website
-   **ATO GST invoice requirements** — ato.gov.au/business

### Regular (subscribe/bookmark)

-   **OAIC newsroom** — RSS for breach notifications and new guidance
-   **DISR news** — where AU AI policy is driven
-   **ACCC announcements** — AI + consumer law intersections
-   **ISO/IEC 42001** — when we're ready for enterprise RFPs, this is the management-system standard

### Deep dives when you have a weekend

-   **NIST AI RMF 1.0** — US framework; best structured thinking on AI risk
-   **EU AI Act summary (not the 400 pages)** — future-proofing
-   **OECD AI Principles** — the global baseline almost all frameworks flow from

---

## 9. Pocket Mental Models

Four models to run every feature through. If any fails, redesign.

### Model 1 — "The Regulator Test"
*If an OAIC or ATO auditor read this code and this UX, would they be comfortable?*

### Model 2 — "The Steve Test"
*If Pip sends this on my behalf, will I still be proud of it in 6 months? Can I stand behind it?*

### Model 3 — "The Front-Page Test"
*If this feature was on the front page of the SMH with a negative headline, what would it look like?*

### Model 4 — "The Trust Test"
*Does this feature make Steve trust us more, or does it make him dependent on us? We want the first.*

---

## 10. Your First Move If Something Goes Wrong

If you suspect a breach, hallucination-caused harm, or regulatory issue:

1.  **Don't panic-delete.** Preserve logs, the prompt, the output, the user's action.
2.  **Contain.** Disable the feature flag or take the endpoint offline. Prefer surgical over nuclear.
3.  **Assess scope.** How many users? What data? Is it an "eligible data breach" under NDB?
4.  **Escalate.** Tell the founder/CTO within the hour. If that's you, tell a trusted advisor.
5.  **Decide notification.** NDB = 30 days to OAIC + users. If it's AI output harm, notify the affected customer directly.
6.  **Fix the root cause.** Add a control, update the prompt, add a guardrail.
7.  **Write it up.** Post-mortem in `docs/postmortems/`. No blame. What happened, what changed, what's different going forward.

---

## 11. The One-Sentence North Star

> **Build the tool Steve would want his daughter to use if she became a tradie.**

If every feature can pass that filter, the rest of this document is just paperwork.

---

**Document Owner:** You  
**Last Reviewed:** 2026-04-13  
**Next Scheduled Review:** 2026-07-13 (or on any regulatory update)