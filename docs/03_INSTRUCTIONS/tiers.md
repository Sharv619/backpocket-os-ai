# Twin Instructions: Email Triage Rules

> **Version:** 1.0 (Created 2026-04-11)
> **Source:** Extracted from SOP.md and SYSTEM_CONTEXT.md
> **Purpose:** Rules the Twin uses to categorize emails

---

## The 5-Tier System

| Tier | Name | Description | Action |
|------|------|-------------|--------|
| **Tier 1** | Priority | Active clients needing help NOW | **Stay in Inbox** - WhatsApp nudge |
| **Tier 2** | Sales/New | New friends, leads, inquiries | **Stay in Inbox** - Draft response |
| **Tier 3** | General | Questions, routine business | **Stay in Inbox** - Professional reply |
| **Tier 4** | Updates | News, thank you notes, digests | **Archive** - Log to Portal_Updates |
| **Tier 5** | Spam | Junk, marketing, promotions | **Trash** - Auto-delete |

---

## Tier 1: Priority (Active Clients)

**Rule:** Any email from existing clients or golden senders

**Golden Senders (Tier 1 - forced):**
- `jco064690@gmail.com`
- `trustdeed.com.au`
- `gjcctax.au`
- `cqstax.com`
- `almemmolos@gmail.com`
- `johnwatts.com.au`
- `david@vdmandthorn.com`

**Client Domain Shield:**
- Any email from a domain in Clients_Master sheet = Tier 1

**Action:** Stay in Inbox, send WhatsApp notification immediately

---

## Tier 2: Govt/Assoc (Special Shields)

**Rule:** Government and association emails that need attention

**Government Domains (Tier 2 - forced):**
- `ato.gov.au`
- `asic.gov.au`
- `ndiscommission.gov.au`

**Association Domains (Tier 2 - forced):**
- `auditorsinstitute.com`
- `auditorsintitute.com` (typo included)
- `publicaccountants.org.au`
- `ifpa.com.au`

**Business Systems (Tier 2 - forced):**
- `stripe.com`
- `cloudoffis`

**Special Triggers:**
- "Document has been signed" → Tier 2 (log to Portal_Updates)
- "New user registered" → Tier 1 (auto-onboarding)
- Business 1300 Call Centre → Tier 2 (notify immediately)

**Action:** Stay in Inbox, draft response ready

---

## Tier 3: Suppliers & Subscriptions

**Rule:** Recurring bills, suppliers, subscriptions

**Known Suppliers (Tier 3 - forced):**
- `superloop.com`
- `bigbosscleaning.com.au`
- `whapi.cloud`
- `telstra.com`
- `nab.com.au`
- `anz.com`
- `appsumo.com`
- `pinch.com.au`
- `suitedash.com`
- `linkedin.com`
- `simplefund360`

**Action:** Archive email + Log to "Govt_Assoc_Log" sheet

---

## Tier 4: Updates & Digests

**Rule:** Automated notifications, digests, routine updates

**Triggers:**
- Subject contains: "notification", "digest", "daily update", "system alert"
- Portal digests (Suitedash planning daily digest)
- Simple politeness: "thanks", "thank you", "ok", "got it" (under 5 words)

**Special Cases:**
- Suitedash Portal Digest with activity → Notify + Log to Portal_Updates
- Suitedash Portal Digest with NO activity → Archive silently

**Action:** Archive + Log to "Portal_Updates" sheet

---

## Tier 5: Spam

**Rule:** Marketing, promotions, junk

**Keywords (Tier 5 - forced):**
- "unsubscribe"
- "no-reply" (in subject)
- "promotion"
- "marketing"
- "offering 50%"
- "lottery"

**Action:** Move to Trash immediately

---

## Special Flows

### Onboarding Flow
1. "New user registered" detected → Extract name/email
2. Add to Clients_Master sheet
3. Send WhatsApp: "NEW CLIENT ONBOARDED!"

### Document Signed Flow
1. "Document has been signed" detected
2. Log to Portal_Updates (not Action_Log)
3. Keep in Inbox (don't archive)
4. Notify via WhatsApp

### QuickBooks Rule
- From: `quickbooks@intuit.com` + "invoice" in subject
- Move to "Quickbooks Recurring Invoice" label

---

## The "Rowan Rule"
> If sender is a client (in Clients_Master), ALWAYS send WhatsApp nudge regardless of tier.

This ensures no client emails are missed.

---

## Cost-Saving Layers

### Layer 0: Rule-Based (FREE)
- All whitelist overrides run first
- No AI calls for known senders
- Spam keywords caught instantly

### Layer 1: Gemini Batch (Cheap)
- Groups 5 emails together
- Single API call for 5 emails
- Saves 80-90% on API costs

### Layer 2: Ollama Fallback (FREE)
- If Gemini fails/timeout
- Uses local qwen2.5:7b model
- Zero cost, offline capable

---

## Related Files

- `01_USER_GUIDES/SOP.md` - Full user manual
- `02_SYSTEM/SYSTEM_CONTEXT.md` - Technical context
- `services/gemini.py` - Actual implementation (pre_triage_rules function)

---

*Last updated: 2026-04-11*