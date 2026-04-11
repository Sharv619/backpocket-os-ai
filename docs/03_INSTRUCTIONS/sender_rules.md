# Sender-Specific Instructions

> **Purpose:** Instructions for specific email senders
> **Storage:** SQLite `sender_instructions` table + Google Sheets

---

## Golden Senders (Tier 1 Priority)

These senders always get Tier 1 treatment - stay in inbox, send WhatsApp nudge.

| Email/Domain | Category | Instructions |
|--------------|----------|--------------|
| `jco064690@gmail.com` | builder | My builder - add to Builder_Tracker, compare quotes |
| `trustdeed.com.au` | professional | Trust deed specialist - high priority |
| `gjcctax.au` | tax_agent | Tax agent - urgent tax matters |
| `cqstax.com.au` | tax_agent | Tax agent - respond quickly |
| `almemmolos@gmail.com` | client | Important client - personal service |
| `johnwatts.com.au` | client | John Watts - priority client |
| `david@vdmandthorn.com` | solicitor | Lawyer - legal matters take priority |

---

## Government & Associations (Tier 2)

| Email/Domain | Category | Instructions |
|--------------|----------|--------------|
| `*@ato.gov.au` | government | ATO - always important, check for deadlines |
| `*@asic.gov.au` | government | ASIC - regulatory matters |
| `*@auditorsinstitute.com` | association | IPA member - professional matters |
| `*@ifpa.com.au` | association | IFPA - financial planning association |
| `*@ndiscommission.gov.au` | government | NDIS - check for compliance items |

---

## Business Systems (Tier 2)

| Email/Domain | Category | Instructions |
|--------------|----------|--------------|
| `*@stripe.com` | payment | Stripe - check for payment issues |
| `messages@business1300.com.au` | call_centre | Business 1300 - always notify immediately |
| `*@cloudoffis.com` | software | Cloud software - check for updates |

---

## Suppliers (Tier 3)

Archive and log to Supplier_Expenses sheet.

| Email/Domain | Category | Instructions |
|--------------|----------|--------------|
| `*@telstra.com` | telecom | Telstra bill |
| `*@nab.com.au` | bank | NAB statements |
| `*@anz.com` | bank | ANZ statements |
| `*@superloop.com` | internet | Internet bill |
| `*@bigbosscleaning.com.au` | cleaning | Cleaning services |

---

## Clients (Dynamic)

Clients are dynamically loaded from `BPS_Client_Master` Google Sheet.

- Any client email = Tier 1
- "Rowan Rule" applies: Always notify via WhatsApp

---

## How to Add New Sender Instructions

### Via Dashboard
1. Go to Dashboard > Instructions tab
2. Click "Add Sender Rule"
3. Enter email, category, instructions
4. Save

### Via API
```bash
curl -X POST http://localhost:8000/api/sender-instruction \
  -H "Content-Type: application/json" \
  -d '{"sender_email": "new@client.com", "instructions": "Important client", "category": "client"}'
```

### Via WhatsApp
Coming soon: "add sender" command

---

## Related

- `03_INSTRUCTIONS/tiers.md` - General tier rules
- `services/database.py` - `save_sender_instruction()` function
- `services/twin_brain.py` - `get_sender_instructions()` function