# Workflows — BackPocket MVP

> Complete workflow definitions for all business processes.
> Last updated: 2026-04-18

---

## 1. Construction Job Lifecycle (9 Stages)

The core business workflow for a tradie/construction job from inquiry to completion.

### Stage Flow

```
[1] Client Inquiry / Call for Quote
 ↓
[1.5] Onsite Inspection Booking
 ↓
[2] Collect Photos & Measurements Onsite
 ↓
[3] Contact Suppliers for Material Quotes
 ↓
[4] Receive Supplier Quotes → Generate Client Quote
 ↓
[5] Send Quote to Client
 ↓
[6] Negotiation ──→ BRANCH
      ├── Accepted → [7] Purchase + Assign + Invoice + Review
      └── Refused  → Pipeline ends
 ↓
[7] Purchase from Supplier, Assign Handyman, Send Invoice, Request Review
 ↓
[9] Issue Lifetime Warranty Paper
```

### Stage Details

| Stage | Title | Trigger | Next Step | Type |
|-------|-------|---------|-----------|------|
| 1 | Client Inquiry / Call for Quote | New email/call/lead | Book onsite inspection | linear |
| 1.5 | Onsite Inspection Booking | Inquiry received | Send confirmation + calendar invite | linear |
| 2 | Collect Photos & Measurements | Inspection date arrives | Contact suppliers | linear |
| 3 | Contact Suppliers | Photos/measurements collected | Wait for supplier quotes | linear |
| 4 | Generate Client Quote | Supplier quotes received | Apply 30% markup, generate quote | linear |
| 5 | Send Quote to Client | Quote finalized | Wait for client response | linear |
| 6 | Negotiation | Client responds | Accept or refuse | branch |
| 7 | Purchase + Assign + Invoice | Quote accepted | Execute job, invoice, request review | linear |
| 9 | Issue Warranty | Job complete + paid | Pipeline complete | linear |

### Auto-Advance Rules

| Event | From Stage | To Stage |
|-------|-----------|----------|
| Lead created | — | 1 |
| Quote created (draft) | 1-3 | 4 |
| Quote status → sent | 4 | 5 |
| Quote status → accepted | 5-6 | 7 |
| Payment received (full) | 7 | 9 |

---

## 2. Lead → Quote → Payment Pipeline

### Lead Status Flow

```
new → quoted → accepted → completed
```

| Status | Meaning | Color |
|--------|---------|-------|
| new | Fresh lead, no quote yet | Blue |
| quoted | Quote created and/or sent | Amber |
| accepted | Client accepted quote | Green |
| completed | Job done + paid | Gray |

### Quote Status Flow

```
draft → sent → accepted → invoiced
```

| Status | Meaning | Color |
|--------|---------|-------|
| draft | Being prepared | Gray |
| sent | Sent to client | Amber |
| accepted | Client agreed | Green |
| invoiced | Invoice generated | Blue |

### Payment Status Flow

```
pending → received
```

### Pipeline Calculation

```
Revenue Pipeline = SUM(total_amount) WHERE status IN ('sent', 'accepted')
Conversion Rate  = COUNT(accepted) / COUNT(sent) * 100
Average Deal     = AVG(total_amount) WHERE status = 'accepted'
```

---

## 3. Email Approval Workflow

### Tier Classification

| Tier | Label | Action | Response Time |
|------|-------|--------|---------------|
| 1 | URGENT | Draft + WhatsApp + Dashboard | < 1 hour |
| 2 | HIGH | Draft + Dashboard | < 4 hours |
| 3 | MEDIUM | Log to sheets | < 24 hours |
| 4 | LOW | Archive + log | When convenient |
| 5 | SPAM | Auto-archive | Never |

### Approval Flow

```
Email arrives
 ↓
AI classifies tier (1-5)
 ↓
Tier 1-2: AI drafts response → pending_approvals table
 ↓
User reviews on dashboard/mobile
 ↓
Approve → send email → log to sheets → WhatsApp confirmation
  OR
Revise → AI refines draft → back to review
  OR
Archive → log to sheets → remove from pending
```

### Email Processing (Background Service)

```
inbox_polling_loop_once() runs every 5 minutes
 ↓
Fetch unread from all Gmail accounts
 ↓
Batch triage: AI classifies tier + generates draft
 ↓
T1/T2: save to pending_approvals + WhatsApp notify
T3: log to sheets
T4: log to Portal_Updates sheet
T5: auto-archive (spam)
```

---

## 4. Voice Command Workflow

### State Machine

```
IDLE → CLASSIFYING → COLLECTING → CONFIRMING → EXECUTING → COMPLETE
                         ↑              |
                         └──────────────┘ (needs more params)
```

### Voice Flow

```
User taps mic → overlay opens
 ↓
Speech-to-text (Whisper API)
 ↓
Intent classification (Gemini 2.5-flash)
 ↓
Confidence check:
  < 0.4 → clarify ("Did you mean...?")
  0.4-0.7 → disambiguate (show options)
  > 0.7 → proceed
 ↓
Parameter check:
  All present → confirm action
  Missing → collect one-by-one (multi-turn)
 ↓
Confirmation:
  Tier A (read-only) → auto-execute
  Tier B (create/update) → verbal "yes"
  Tier C (send/delete) → key phrase ("say 'send it' to confirm")
 ↓
Execute → TTS response → UI action (navigate/refresh/highlight)
```

### Screen-Specific Intents (Key Examples)

| Screen | Intent | Example Utterance |
|--------|--------|-------------------|
| Dashboard | dashboard.summary | "What's going on today?" |
| Inbox | inbox.approve | "Approve the one from John" |
| Inbox | inbox.filter_tier | "Show me urgent ones" |
| Construction | construction.lead.create | "New lead, Sarah, kitchen reno in Penrith" |
| Construction | construction.quote.create | "Chuck a quote together for that Penrith job" |
| Construction | construction.payment.record | "Mark the Thompson payment as received" |
| Cross-screen | cross.email_to_lead | "Turn that email into a lead" |
| Cross-screen | cross.lead_to_quote | "Create a lead and quote for this email" |

---

## 5. Email → Lead Extraction Workflow

```
User views email in inbox
 ↓
Taps "Extract Lead" button
 ↓
POST /api/construction/leads/extract
  Body: { from, subject, body }
 ↓
AI extracts: client_name, job_type, location, scope_items, urgency, estimated_budget
 ↓
Preview dialog shows extracted fields (editable)
 ↓
User confirms → lead saved → optional navigate to construction
```

---

## 6. Quote → Invoice Workflow

```
Quote status = accepted
 ↓
User taps "Generate Invoice"
 ↓
POST /api/invoice/generate
  Body: { client_name, client_email, items, notes }
 ↓
PDF generated with:
  - Auto invoice number
  - 14-day payment terms
  - Line items from quote
 ↓
PDF preview → download/email to client
```

---

## 7. Marketing — GBP Post Workflow

```
User completes a job
 ↓
Goes to Marketing tab → "New GBP Post"
 ↓
Enters: suburb + job description
 ↓
AI generates 2-sentence local post
 ↓
Preview → edit → mark as posted
 ↓
Saved to marketing_activity table
```

---

## 8. Document Analysis Workflow

```
User uploads document (invoice, receipt, plan)
 ↓
Vision API analyzes image/PDF
 ↓
Extracted data displayed (amounts, dates, line items)
 ↓
Option to: save to RAG, attach to quote, or log
```

---

## 9. Business Instructions Workflow

```
User creates instruction (e.g., "Always reply within 4 hours to tier 1")
 ↓
Saved to instructions table with category (tone/workflow/priority/style/compliance)
 ↓
Instructions loaded into AI prompt context during email triage + voice responses
 ↓
Revision history tracked for auditing
```
