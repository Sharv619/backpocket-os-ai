# BackPocket - Specialized Construction/Tradie Workflows

Advanced automation for construction contractors, electricians, plumbers, and trade professionals using AI-powered lead management and follow-ups.

---

## 🏗️ Lead-to-Scope Extractor Workflow

**Status:** Production Ready  
**Timeline:** Automatic (< 30 seconds per email)  
**Key Twin:** Accountant (for scope & budget)

### Overview
When a potential client emails about a job, BackPocket instantly extracts structured data to feed directly into your quote workflow. No more manual note-taking.

### How It Works

```
NEW EMAIL ARRIVES
    ↓
SYSTEM DETECTS "INQUIRY" PATTERN
    ↓
ACCOUNTANT TWIN ANALYZES
    ↓
EXTRACTS STRUCTURED JSON
    ↓
STORES IN LEADS TABLE
    ↓
AUTO-TRIGGERS QUOTE WORKFLOW
```

### The Extraction Process

#### Input: Raw Email
```
From: Sarah Johnson <sarah@emailprovider.com>
Subject: Kitchen renovation - our old kitchen is falling apart

Hi there,

We're looking to renovate our kitchen. The cabinets are falling apart, 
the tiles are outdated, and we need soft-close drawers installed. 
The budget is around $15k and we want it done before summer starts 
(about 2-3 months). We're in Penrith.

Can you send through a quote?

Thanks,
Sarah
```

#### AI Processing
The Accountant Twin runs this prompt:

```
Act as a specialized construction estimator. Analyze the following email 
from a potential client.

Extract the following JSON structure:
- client_name: (Full name)
- job_type: (e.g., Kitchen Reno, Deck, Emergency Repair)
- location: (Street address if mentioned)
- pain_points: (List specific problems mentioned)
- scope_items: (List specific items to be quoted)
- urgency: (High/Medium/Low based on tone)
- estimated_budget: (if mentioned)
- timeline: (if mentioned)
- contact_info: (phone, email)

Email Content:
[EMAIL BODY]
```

#### Output: Structured Data
```json
{
  "client_name": "Sarah Johnson",
  "email": "sarah@emailprovider.com",
  "job_type": "Kitchen Renovation",
  "location": "Penrith, NSW",
  "pain_points": [
    "Cabinets falling apart",
    "Tiles outdated",
    "Need modern cabinetry"
  ],
  "scope_items": [
    "Cabinet replacement",
    "Soft-close drawers",
    "Tile work"
  ],
  "urgency": "High",
  "estimated_budget": 15000,
  "timeline": "2-3 months",
  "confidence_score": 0.95
}
```

### What Happens Next

1. **Data Stored**: LED entry created in `construction_leads` table
2. **Auto-Match**: System checks past similar jobs for pricing
3. **Draft Quote**: Accountant Twin generates rough estimate
4. **Notification**: Alert sent to you with extracted details
5. **Dashboard**: New lead appears in "Quotes to Generate" section

### Database Table

```sql
construction_leads (
  id PRIMARY KEY,
  client_name TEXT,
  email TEXT,
  job_type TEXT,
  location TEXT,
  pain_points JSON,
  scope_items JSON,
  estimated_budget DECIMAL,
  timeline TEXT,
  urgency TEXT,
  extraction_confidence FLOAT,
  raw_email_id TEXT,
  quote_id TEXT (FK),
  created_at TIMESTAMP,
  processed_at TIMESTAMP
)
```

### API Endpoint

```bash
# Manually trigger extraction (if auto-detection fails)
POST /api/construction/extract-lead
{
  "email_id": "msg123",
  "subject": "Kitchen renovation inquiry",
  "from": "sarah@example.com",
  "body": "We're looking to renovate our kitchen..."
}
→ Returns: {
    client_name,
    job_type,
    location,
    pain_points,
    scope_items,
    urgency,
    estimated_budget,
    timeline,
    quote_template_id
  }

# Get all extracted leads
GET /api/construction/leads?status=pending_quote
→ Returns: [{ lead }, { lead }, ...]
```

### Accuracy & Fallbacks

- **High Confidence (>0.85)**: Auto-create draft quote
- **Medium Confidence (0.5-0.85)**: Create lead, flag for review
- **Low Confidence (<0.5)**: Flag as uncertain, show to user for manual review

### Example: Real-World Flow

```
10:42 AM - Email arrives: "Kitchen reno needed ASAP"
10:42 AM - System extracts: {client: "John", job: "Kitchen", urgency: "High"}
10:43 AM - Dashboard pops up alert: "New High-Urgency Lead: John - Kitchen Reno"
10:43 AM - You click lead → see full details + suggested quote template
10:45 AM - You customize quote and send
11:20 AM - Client replies with "looks good, let's book"
```

---

## 💬 Tradie Persona Follow-up Workflow

**Status:** Production Ready  
**Timeline:** Automatic, customizable schedule (3-7 days post-quote)  
**Key Twin:** Admin (for tone & timing)

### Overview
Stop sounding like a robot. Let your AI Digital Twin send friendly, professional follow-ups that actually get responses—without the corporate speak.

### How It Works

```
QUOTE SENT TO CLIENT
    ↓
AUTO-SCHEDULE FOLLOW-UP (3-7 days)
    ↓
ADMIN TWIN GENERATES PERSONA MESSAGE
    ↓
USER REVIEWS & APPROVES
    ↓
SEND VIA EMAIL/SMS (at optimal time)
    ↓
TRACK RESPONSE (updated in CRM)
```

### The Prompt Structure

```
You are an AI Digital Twin for a professional contractor in Western Sydney.

Personality Traits:
- Professional and reliable ("no-nonsense")
- Friendly and approachable (not stiff)
- Honest and direct (no sales fluff)
- Local knowledge (knows the area)
- Values the client's time

Task: Draft a follow-up message for a quote sent 4 days ago to 
[CLIENT NAME] regarding [JOB TYPE].

Constraints:
✓ Keep it under 60 words
✓ No corporate speak ("per our previous correspondence", "going forward")
✓ Use casual, respectful closings: "Cheers", "Let me know", "Thanks mate"
✓ Include subtle scheduling nudge ("next month's filling up")
✓ Sound like a person, not AI
✓ Show you remember their specific job
✓ One clear next step (call/email/site visit)
```

### Example: Generated Follow-ups

**Kitchen Reno (4 days post-quote):**
```
Hi Sarah,

Just checking in on that kitchen reno quote. Still interested? 
Next month's already looking pretty full, so keen to lock you in 
if you're ready to go. Give me a call if you've got any questions.

Cheers,
Himanshu Lade
```

**Emergency Repair (2 days post-quote):**
```
Sarah,

Got your kitchen situation sorted in that quote I sent. If you want 
to move fast, I've got a spot opening up this week. Otherwise, happy 
to chat about timing.

Let me know!

Himanshu Lade
```

**Deck Build (7 days post-quote):**
```
Hi John,

Haven't heard back on the deck quote yet. Still want to chat through 
the options? I'm free for a quick call this Friday if that works.

Cheers,
Himanshu Lade
```

### Customization Options

User can set:
- **Tone**: Professional, Friendly, Casual, Technical
- **Follow-up Timing**: 2, 3, 5, or 7 days after quote
- **Channel**: Email, SMS, WhatsApp, or Mix
- **Personality**: "No-nonsense tradie", "Friendly local pro", "Technical expert"
- **Urgency Level**: Subtle, Moderate, High pressure (optional)

### Database Table

```sql
tradie_followups (
  id PRIMARY KEY,
  lead_id FK,
  quote_id FK,
  client_name TEXT,
  client_phone TEXT,
  job_type TEXT,
  scheduled_for TIMESTAMP,
  channel TEXT (email|sms|whatsapp),
  draft_message TEXT,
  tone TEXT,
  approved_by TEXT,
  approved_at TIMESTAMP,
  sent_at TIMESTAMP,
  response_received BOOLEAN,
  response_text TEXT,
  response_at TIMESTAMP
)
```

### API Endpoint

```bash
# Generate follow-up message
POST /api/construction/followup/generate
{
  "quote_id": "q123",
  "client_name": "Sarah Johnson",
  "job_type": "Kitchen Renovation",
  "days_since_quote": 4,
  "tone": "no-nonsense",
  "channel": "email",
  "urgency": "subtle"
}
→ Returns: {
    draft_message,
    suggestions: ["Alternative opening", "Better closing"],
    sentiment_score,
    estimated_response_rate
  }

# Approve & schedule send
POST /api/construction/followup/approve
{
  "followup_id": "f456",
  "approved_message": "Hi Sarah...",
  "send_at": "2024-04-15T09:00:00Z"
}
→ Returns: { status, scheduled_for, channel }

# Track responses
GET /api/construction/followup/responses?quote_id=q123
→ Returns: {
    sent_at,
    channel,
    response_received,
    response_text,
    response_at,
    next_action
  }
```

### Real-World Automation

```
DAY 1: Quote sent to Sarah
DAY 4: System auto-drafts follow-up message (you review)
DAY 4: You approve, system sends at 9:15 AM
DAY 4: Sarah replies "Love it, book us in"
DAY 4: System creates entry in `approved_quotes` table
DAY 5: System sends "Great! Let's get you scheduled" confirmation
```

---

## 🎙️ Site Note to Action Items Workflow

**Status:** Production Ready  
**Timeline:** Automatic (< 1 minute per recording)  
**Key Twin:** Auditor (for structure & accuracy)

### Overview
Record a quick voice memo after site visits. BackPocket converts it to a structured site report with material lists, subcontractor calls, client promises, and the #1 next action.

### How It Works

```
RECORD VOICE NOTE (30-60 seconds)
    ↓
SPEECH-TO-TEXT CONVERSION
    ↓
AUDITOR TWIN ANALYZES TRANSCRIPT
    ↓
EXTRACTS STRUCTURED DATA
    ↓
CREATES ACTION ITEMS
    ↓
STORES IN SITE REPORTS TABLE
    ↓
NOTIFIES TEAM
```

### The Voice-to-Text Process

#### Example Recording (Raw Transcript)
```
"Right, just left the Johnson kitchen job. So the cabinets are worse 
than I thought, gonna need to replace the whole run. Couple boards 
are water damaged. Need to order meranti timber, probably 50 metres, 
and some soft-close hinges. I told them I'd send the color palette 
by Tuesday - gotta remind myself about that. Also need to call sparky 
about the light recess, it's not gonna fit with the new cabinet 
height. Main thing is I gotta get the timber ordered by Friday or 
we're looking at a two-week delay. Oh, also need to send them a 
revised quote for the extra work."
```

#### AI Processing
The Auditor Twin runs this prompt:

```
Convert this raw voice-to-text transcript into a structured site report.

Analyze and identify:

1. Materials to Order
   - Specific materials (timber type, dimensions)
   - Quantity
   - Vendor (if mentioned)
   - Urgency

2. Subcontractors to Call
   - Trade (sparky, plumber, etc.)
   - Reason for call
   - Urgency

3. Client Promises
   - What you promised to send/do
   - Deadline
   - Status

4. Issues/Observations
   - Scope changes
   - Additional costs
   - Site conditions that affect work

5. Next Step
   - The SINGLE most important next action
   - Deadline
   - Owner (you / team member)

Transcript:
[TRANSCRIPT TEXT]
```

#### Output: Structured Report
```json
{
  "site_visit_id": "sv-2024-04-15-johnson",
  "location": "Johnson Kitchen",
  "visit_date": "2024-04-15T14:30:00Z",
  "duration_minutes": 45,
  "materials_to_order": [
    {
      "item": "Meranti timber (cabinet run)",
      "quantity": "50 metres",
      "vendor": "Not specified",
      "urgency": "HIGH",
      "deadline": "2024-04-19",
      "notes": "Water damage found, full cabinet replacement needed"
    },
    {
      "item": "Soft-close hinges",
      "quantity": "TBD",
      "vendor": "Not specified",
      "urgency": "HIGH",
      "deadline": "2024-04-19"
    }
  ],
  "subcontractors_to_call": [
    {
      "trade": "Electrician (sparky)",
      "reason": "Light recess height conflict with new cabinet height",
      "urgency": "HIGH",
      "contact": "Not in system"
    }
  ],
  "client_promises": [
    {
      "promise": "Send color palette",
      "deadline": "2024-04-16",
      "status": "PENDING",
      "reminder": true
    }
  ],
  "scope_changes": [
    {
      "change": "Water damage requires full cabinet run replacement",
      "impact": "Increased cost",
      "action": "Send revised quote to client"
    }
  ],
  "next_steps": [
    {
      "priority": 1,
      "action": "Order meranti timber",
      "deadline": "2024-04-19",
      "owner": "You",
      "reason": "Two-week delay if missed"
    },
    {
      "priority": 2,
      "action": "Call electrician about light recess",
      "deadline": "2024-04-16",
      "owner": "You"
    },
    {
      "priority": 3,
      "action": "Send revised quote to Johnson",
      "deadline": "2024-04-17",
      "owner": "You"
    }
  ],
  "confidence_score": 0.92
}
```

### Integration Points

1. **Materials → Procurement System**
   - Auto-create PO (if vendor configured)
   - Add to shopping list
   - Send email to supplier

2. **Subcontractors → Call Stack**
   - Add to "Calls to Make" section
   - Log call when made
   - Record date/cost

3. **Client Promises → Reminders**
   - Calendar event created
   - SMS reminder on deadline
   - Flagged in CRM

4. **Action Items → Task Dashboard**
   - Sorted by priority & deadline
   - Assigned to team members
   - Track completion

### Database Tables

```sql
site_visits (
  id PRIMARY KEY,
  location TEXT,
  client_id FK,
  job_id FK,
  visit_date TIMESTAMP,
  transcript TEXT,
  raw_audio_path TEXT,
  processed_report_json TEXT,
  confidence_score FLOAT,
  created_at TIMESTAMP
)

site_materials (
  id PRIMARY KEY,
  site_visit_id FK,
  item TEXT,
  quantity TEXT,
  vendor TEXT,
  urgency TEXT,
  deadline TIMESTAMP,
  ordered_at TIMESTAMP,
  po_id TEXT
)

site_subcontractors (
  id PRIMARY KEY,
  site_visit_id FK,
  trade TEXT,
  reason TEXT,
  urgency TEXT,
  contact_id FK,
  called_at TIMESTAMP,
  notes TEXT
)

site_action_items (
  id PRIMARY KEY,
  site_visit_id FK,
  action TEXT,
  priority INT,
  deadline TIMESTAMP,
  owner TEXT,
  status TEXT (pending|in_progress|completed),
  completed_at TIMESTAMP
)
```

### API Endpoints

```bash
# Submit voice recording
POST /api/construction/site-visit/audio
Content-Type: multipart/form-data

FormData:
  - audio_file: (binary)
  - location: "Johnson Kitchen"
  - job_id: "job123"
  - client_id: "client456"

→ Returns: { site_visit_id, processing_status }

# Process transcript (auto-called after speech-to-text)
POST /api/construction/site-visit/process
{
  "site_visit_id": "sv123",
  "transcript": "Right, just left the Johnson kitchen..."
}
→ Returns: {
    materials: [...],
    subcontractors: [...],
    client_promises: [...],
    action_items: [...],
    confidence_score
  }

# Get site report
GET /api/construction/site-visit/{site_visit_id}
→ Returns: { full_structured_report }

# Get pending action items
GET /api/construction/action-items?sort=priority&status=pending
→ Returns: [{ action_item }, { action_item }, ...]

# Complete action item
PATCH /api/construction/action-items/{item_id}
{
  "status": "completed",
  "notes": "Timber ordered from ABC Lumber"
}
→ Returns: { updated_item }
```

### Real-World Workflow

```
2:30 PM - Site visit complete, you record 45-second voice note
2:32 PM - System converts to text
2:33 PM - Auditor Twin extracts data
2:34 PM - Dashboard updates:
         - 2 materials added to procurement list
         - Sparky added to "Calls to Make"
         - "Send palette" reminder set for Tuesday 9 AM
         - "Order timber by Friday" flagged as HIGH priority
3:00 PM - You review the extracted report (90% confident)
3:01 PM - You click "Order Timber" → automatically creates email draft to supplier
3:05 PM - You review and send purchase email
```

---

## 📊 Integration Across All Three Workflows

These three workflows work together seamlessly:

```
EMAIL ARRIVES
    ↓
LEAD-TO-SCOPE EXTRACTOR → Creates lead + quote template
    ↓
QUOTE SENT TO CLIENT
    ↓
TRADIE PERSONA FOLLOW-UP → Sends friendly reminder (Day 3-5)
    ↓
CLIENT SAYS YES + SITE VISIT SCHEDULED
    ↓
SITE VISIT COMPLETE
    ↓
SITE NOTE TO ACTION ITEMS → Creates material list + action items
    ↓
NEXT JOB SCHEDULED
```

Each workflow feeds data into the system that helps subsequent workflows:
- Lead info → used in follow-up messages
- Client promises → reminder system
- Materials ordered → job budget tracking
- Action items → completion reporting for client satisfaction

---

## Advanced Features

### Learning & Optimization
- Each workflow learns from your corrections
- AI models adjust tone/format based on your preferences
- Accuracy improves over time

### Team Collaboration
- Assign action items to team members
- Track completion
- Monitor material deliveries
- Alert on missed deadlines

### Reporting
- Monthly site visit summary
- Material ordering patterns
- Response rates on follow-ups
- Time to completion tracking

---

## Troubleshooting

**Q: Extraction not accurate for my industry**
A: Edit the extraction prompt in Settings → Customize Prompts

**Q: Follow-ups sound too formal/casual**
A: Adjust tone setting (Professional/Friendly/Casual/Technical)

**Q: Site notes missing important details**
A: Speak slower, mention items by name, be specific about quantities

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for more help.
