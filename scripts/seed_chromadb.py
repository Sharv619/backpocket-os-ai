"""
Seed ChromaDB with ATO + Fair Work compliance knowledge.
Run once: python scripts/seed_chromadb.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.twin_engine import ingest_document

# ── ATO / Tax knowledge (Accountant Twin) ─────────────────────────────────────
ACCOUNTANT_DOCS = [
    ("ato-gst-basics", """Australian GST (Goods and Services Tax):
- 10% GST applies to most goods, services, and other things sold or consumed in Australia
- Registered businesses must include GST in their prices
- Small businesses under $75,000 turnover don't need to register for GST
- GST-free items: basic food, health services, education, exports
- Input tax credits: you can claim GST credits for business purchases
- BAS (Business Activity Statement) reports GST collected and paid"""),

    ("ato-tax-invoice-requirements", """ATO Tax Invoice Requirements:
A valid tax invoice must include:
- The words 'Tax Invoice' prominently displayed
- Seller's name and ABN (Australian Business Number)
- Date of issue
- Brief description of the goods/services sold
- GST amount (or statement that total includes GST)
- For invoices $1000+: buyer's name and address
- GST-exclusive price AND GST amount shown separately
Invoices under $82.50 (inc GST) don't need to be tax invoices"""),

    ("ato-bas-reporting", """BAS (Business Activity Statement) Reporting:
- Monthly BAS: turnover $20M+ per year
- Quarterly BAS: turnover under $20M (most sole traders)
- Annual BAS option: turnover under $75K (GST-registered voluntarily)
- Report: GST collected, GST paid (input tax credits), PAYG withholding
- Due dates: quarterly BAS due 28th of the month following each quarter
- Q1 Jul-Sep: due 28 Oct | Q2 Oct-Dec: due 28 Feb | Q3 Jan-Mar: due 28 Apr | Q4 Apr-Jun: due 28 Jul
- Lodge via MyBusiness, tax agent, or online"""),

    ("ato-sole-trader-deductions", """Common Sole Trader Tax Deductions:
- Home office expenses (work-related portion)
- Vehicle expenses (business travel, logbook method or cents-per-km)
- Phone and internet (business use percentage)
- Professional subscriptions and memberships
- Accounting and bookkeeping fees
- Marketing and advertising
- Equipment and tools (instant asset write-off up to threshold)
- Professional development and training
- Insurance premiums (business-related)
- Bank fees on business accounts
Must have receipts/records for all claims. Personal expenses NOT deductible."""),

    ("ato-abn-requirements", """ABN (Australian Business Number):
- Required if running a business in Australia
- Apply at abr.gov.au — free, usually issued immediately
- Must be quoted on tax invoices over $82.50
- If supplier doesn't quote ABN, withhold 47% PAYG from payment
- Cancel ABN when ceasing business
- ABN is 11 digits: unique to your business"""),

    ("ato-income-tax-sole-trader", """Sole Trader Income Tax:
- Taxed at personal income tax rates (not company rate)
- Report business income on individual tax return (schedule)
- Tax brackets 2024-25: $0-18,200 (0%), $18,201-45,000 (19%), $45,001-120,000 (32.5%), $120,001-180,000 (37%), $180,001+ (45%)
- Low income tax offset (LITO) reduces tax for lower earners
- Prepay tax via PAYG Instalments (quarterly) to avoid lump sum
- Keep all records for 5 years after lodgment"""),
]

# ── Fair Work knowledge (Auditor + Admin Twins) ───────────────────────────────
AUDITOR_DOCS = [
    ("fw-contractor-vs-employee", """Fair Work: Contractor vs Employee Test:
Key factors that determine if a worker is a contractor or employee:
- Control: employer controls how work is done (employee indicator)
- Integration: work is integral to business (employee indicator)
- Risk: contractor bears financial risk
- Tools: contractor provides own tools
- Exclusivity: employee works only for one business
- Leave entitlements: employees get annual, sick, parental leave
- Superannuation: employers must pay super for employees (11.5% 2024-25)
Misclassification penalties are significant — get it right."""),

    ("fw-invoice-compliance-check", """Invoice Compliance Checklist (Fair Work + ATO):
For contractors/freelancers issuing invoices:
1. ABN included? (required if over $82.50)
2. 'Tax Invoice' heading present?
3. Date of issue included?
4. Clear description of services?
5. GST amount shown separately (or 'Price includes GST')?
6. Payment terms clear?
7. Bank details for EFT payment?
8. Invoice number for tracking?
9. Business name matches ABN registration?
Missing any of these can cause payment delays or ATO issues."""),

    ("fw-payment-terms", """Payment Terms and Fair Work:
- No specific payment term mandated by Fair Work for contractors
- Commercial standard: Net 14 or Net 30 days is common
- Late payment: no automatic penalty but can pursue via courts/QCAT
- For employees: wages must be paid at least monthly
- Subcontractor agreements should specify: payment terms, late fees, dispute resolution
- Written contracts strongly recommended for any engagement over $500"""),

    ("fw-record-keeping", """Fair Work Record Keeping Requirements:
Employers must keep for 7 years:
- Employee pay records (name, employment type, dates employed)
- Hours worked records
- Leave records
- Superannuation records
- Termination records
Sole traders with no employees: keep business records 5 years (ATO requirement)
Digital records are acceptable — must be legible and accessible"""),
]

# ── Admin / email knowledge ───────────────────────────────────────────────────
ADMIN_DOCS = [
    ("admin-email-triage-rules", """Email Triage System for Sole Traders:
Priority tiers:
Tier 1 - Reply needed: Direct client emails, ATO notices, invoices due, urgent requests
Tier 2 - Review needed: General inquiries, status requests, non-urgent business matters
Tier 3 - FYI only: Meeting confirmations, internal updates, auto-notifications
Tier 4 - Archive: Portal updates, system digests, newsletters
Tier 5 - Spam/ignore: Marketing, promotions, unsubscribe candidates
Best practice: Process Tier 1 within 4 hours, Tier 2 within 24 hours"""),

    ("admin-client-follow-up", """Client Follow-Up Best Practices:
- Invoice follow-up: send reminder at 7 days, 14 days, 30 days overdue
- First reminder: friendly reminder tone
- Second reminder: firm, reference invoice number and due date
- Third reminder: formal demand, mention debt collection
- Response time SLA: acknowledge all client emails within 24 hours
- Use CRM notes to track follow-up history
- Automate recurring follow-ups where possible"""),

    ("admin-onboarding-checklist", """New Client Onboarding Checklist:
1. Collect: full name/business name, ABN, email, phone, address
2. Set up client file with unique ID
3. Confirm scope of engagement in writing
4. Issue engagement letter or service agreement
5. Collect signed authority/consent forms
6. Set up for invoicing (rate, payment terms)
7. Add to CRM/client list
8. Send welcome email with contact details
9. Schedule kick-off call or meeting
10. Create folder structure for client documents"""),
]


def main():
    print("Seeding ChromaDB with ATO + Fair Work knowledge...")

    count = 0
    for doc_id, text in ACCOUNTANT_DOCS:
        ok = ingest_document("accountant", doc_id, text, {"source": "ATO"})
        print(f"  accountant/{doc_id}: {'OK' if ok else 'SKIP (chromadb unavailable)'}")
        count += ok

    for doc_id, text in AUDITOR_DOCS:
        ok = ingest_document("auditor", doc_id, text, {"source": "Fair Work AU"})
        print(f"  auditor/{doc_id}: {'OK' if ok else 'SKIP (chromadb unavailable)'}")
        count += ok

    for doc_id, text in ADMIN_DOCS:
        ok = ingest_document("admin", doc_id, text, {"source": "Admin best practice"})
        print(f"  admin/{doc_id}: {'OK' if ok else 'SKIP (chromadb unavailable)'}")
        count += ok

    print(f"\nDone. {count} documents ingested into ChromaDB.")
    if count == 0:
        print("ChromaDB unavailable — install: pip install chromadb")


if __name__ == "__main__":
    main()
