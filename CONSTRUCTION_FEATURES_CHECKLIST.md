# Construction/Tradie Features Implementation Checklist

Based on the wireframes you shared, here's what needs to be added to fully support construction business workflows.

---

## 🎯 FEATURES FROM YOUR SCREENSHOTS

### 1. **Lead Management** 📩
**Screenshot**: Inbox with Sarah Mitchell kitchen renovation lead

**What's Needed**:
- [ ] `leads` table (client_name, email, job_type, location, urgency, status)
- [ ] Lead extraction API endpoint (uses Lead-to-Scope Extractor)
- [ ] Dashboard section showing recent leads
- [ ] Lead detail view with full requirements
- [ ] Lead status tracking (new, quoted, accepted, rejected)

### 2. **Quote Workflow** 💰
**Screenshot**: Quote pipeline with 24 total, 8 pending, 12 accepted, $45,200 revenue

**What's Needed**:
- [ ] `quotes` table (client_id, job_type, amount, status, created_date)
- [ ] Quote generation endpoint
- [ ] Quote template system
- [ ] Status tracking (draft, sent, accepted, declined, invoiced)
- [ ] Revenue pipeline visualization
- [ ] Quote history per client
- [ ] API: `POST /api/quotes/generate`, `GET /api/quotes/pipeline`, `PATCH /api/quotes/{id}`

### 3. **Files & Documents** 📁
**Screenshot**: Kitchen_Quote_Sarah_Mitchell.pdf, Bathroom_Photos_David_Chen.zip, etc.

**What's Needed**:
- [ ] Job-based file organization
- [ ] Link files to quotes/jobs
- [ ] File type handling (PDF, ZIP, JPG)
- [ ] Document preview
- [ ] Upload to specific job
- [ ] API: `POST /api/jobs/{job_id}/files`, `GET /api/jobs/{job_id}/files`

### 4. **AI-Drafted Responses** 🤖
**Screenshot**: "Pip drafted a response" with professional quote reply

**What's Needed**:
- [ ] Use Tradie Persona Follow-up prompt
- [ ] Show drafted response in lead detail
- [ ] Edit before sending
- [ ] Track sent responses
- [ ] Link to email/SMS
- [ ] API: `POST /api/leads/{lead_id}/draft-response`

### 5. **Payment Tracking** 💳
**Screenshot**: "Payment of $2,450 received from David Chen"

**What's Needed**:
- [ ] `payments` table (quote_id, amount, status, date)
- [ ] Invoice generation
- [ ] Payment status tracking
- [ ] Accounting integration
- [ ] Dashboard summary
- [ ] API: `POST /api/payments`, `GET /api/payments`

---

## 📋 IMPLEMENTATION PRIORITY

### **Phase 1: Core Features (Week 1)**
1. ✅ Lead management (database + API)
2. ✅ Quote generation & tracking
3. ✅ Basic dashboard sections
4. ✅ File organization

### **Phase 2: AI Integration (Week 2)**
5. ✅ Lead-to-Scope extractor
6. ✅ Tradie persona follow-ups
7. ✅ Draft response system
8. ✅ Auto-quote generation

### **Phase 3: Advanced (Week 3+)**
9. ⏳ Payment tracking
10. ⏳ Invoice generation
11. ⏳ Revenue reporting
12. ⏳ Mobile integration

---

## 🗄️ DATABASE SCHEMA NEEDED

```sql
-- Leads Table
CREATE TABLE leads (
  id INTEGER PRIMARY KEY,
  client_name TEXT,
  email TEXT,
  phone TEXT,
  job_type TEXT,
  location TEXT,
  pain_points TEXT,  -- JSON
  scope_items TEXT,  -- JSON
  urgency TEXT (HIGH/MEDIUM/LOW),
  estimated_budget DECIMAL,
  timeline TEXT,
  status TEXT (new/quoted/accepted/rejected),
  extracted_at TIMESTAMP,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Quotes Table
CREATE TABLE quotes (
  id INTEGER PRIMARY KEY,
  lead_id INTEGER FK,
  client_id INTEGER FK,
  job_type TEXT,
  description TEXT,
  scope_items TEXT,  -- JSON
  amount DECIMAL,
  materials DECIMAL,
  labor DECIMAL,
  markup DECIMAL,
  status TEXT (draft/sent/accepted/declined/invoiced),
  sent_date TIMESTAMP,
  accepted_date TIMESTAMP,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Payments Table
CREATE TABLE payments (
  id INTEGER PRIMARY KEY,
  quote_id INTEGER FK,
  client_id INTEGER FK,
  amount DECIMAL,
  status TEXT (pending/received/overdue),
  due_date DATE,
  received_date DATE,
  created_at TIMESTAMP
);

-- Job Files Table
CREATE TABLE job_files (
  id INTEGER PRIMARY KEY,
  quote_id INTEGER FK,
  client_id INTEGER FK,
  file_name TEXT,
  file_path TEXT,
  file_type TEXT,
  category TEXT (quote/invoice/site_photo/blueprint),
  uploaded_by TEXT,
  uploaded_at TIMESTAMP
);

-- Site Visits Table
CREATE TABLE site_visits (
  id INTEGER PRIMARY KEY,
  quote_id INTEGER FK,
  visit_date DATE,
  transcript TEXT,
  materials_json TEXT,
  subcontractors_json TEXT,
  action_items_json TEXT,
  created_at TIMESTAMP
);
```

---

## 🔌 API ENDPOINTS NEEDED

### Leads API
```
POST   /api/construction/leads          → Create lead from email
GET    /api/construction/leads          → List all leads
GET    /api/construction/leads/{id}     → Get lead details
PATCH  /api/construction/leads/{id}     → Update lead status
POST   /api/construction/leads/{id}/quote → Generate quote for lead
```

### Quotes API
```
POST   /api/construction/quotes         → Create quote manually
GET    /api/construction/quotes         → List all quotes
GET    /api/construction/quotes/{id}    → Get quote details
PATCH  /api/construction/quotes/{id}    → Update quote (amount, status)
GET    /api/construction/quotes/pipeline → Get pipeline summary
POST   /api/construction/quotes/{id}/send → Send quote to client
POST   /api/construction/quotes/{id}/followup → Generate follow-up
```

### Payments API
```
POST   /api/construction/payments       → Record payment
GET    /api/construction/payments       → List payments
GET    /api/construction/payments/summary → Get payment stats
```

### Files API
```
POST   /api/construction/quotes/{id}/files     → Upload file to quote
GET    /api/construction/quotes/{id}/files     → List quote files
DELETE /api/construction/quotes/{id}/files/{fid} → Delete file
```

---

## 🎨 UI COMPONENTS NEEDED

### Dashboard Sections
- [ ] **Inbox** - Shows recent leads
  - Lead name, email, job type
  - Time received
  - Quick action buttons
  
- [ ] **Quote Pipeline** - Visual overview
  - Total quotes: 24
  - Pending: 8
  - Accepted: 12
  - Revenue: $45,200
  - Charts/visualizations

- [ ] **Recent Files** - File browser
  - File name, size, date
  - File type icons
  - Quick upload
  
- [ ] **Lead Detail** - Full lead view
  - Client info
  - Job requirements
  - Scope items (extracted)
  - Estimated budget
  - AI-drafted response
  - Action buttons: Generate Quote, Follow-up, Schedule Site Visit

- [ ] **Quote Detail** - Quote view
  - Client info
  - Scope breakdown
  - Cost breakdown (materials, labor, markup)
  - Status timeline
  - Actions: Send, Edit, Decline, Accept, Invoice

---

## 🔄 WORKFLOW INTEGRATION

### Lead-to-Scope Extractor Flow
```
EMAIL ARRIVES
    ↓
SYSTEM DETECTS "INQUIRY" PATTERN
    ↓
EXTRACT LEAD DATA
  - client_name
  - job_type
  - location
  - pain_points
  - scope_items
  - urgency
  - estimated_budget
    ↓
STORE IN leads TABLE
    ↓
DASHBOARD ALERT: "New Lead: Sarah Mitchell - Kitchen Reno"
    ↓
USER CLICKS → GENERATE QUOTE
```

### Tradie Persona Follow-up Flow
```
QUOTE SENT TO CLIENT
    ↓
AFTER 3-7 DAYS (CONFIGURABLE)
    ↓
GENERATE FRIENDLY FOLLOW-UP MESSAGE
  - Tone: Professional but friendly
  - Include: Job type, timeline
  - CTA: "Let me know what you think"
    ↓
USER REVIEWS & APPROVES
    ↓
SEND VIA EMAIL/SMS
    ↓
TRACK RESPONSE
```

### Site Note to Action Items Flow
```
USER RECORDS VOICE MEMO AT SITE
    ↓
SPEECH-TO-TEXT CONVERSION
    ↓
AI ANALYZES TRANSCRIPT
    ↓
EXTRACTS:
  - Materials to Order
  - Subcontractors to Call
  - Client Promises
  - Next Steps
    ↓
CREATES ACTION ITEMS
    ↓
UPDATES JOB STATUS
```

---

## 📱 TESTING SCENARIOS

### Test 1: Lead Extraction
```
Input: Email from Sarah Mitchell
Expected:
  - Lead created: Sarah Mitchell
  - Job type: Kitchen Renovation
  - Location: Parramatta
  - Scope: Cabinets, countertops, appliances
  - Budget: ~$12-18k (estimated)
  - Urgency: High (soon mentioned)
```

### Test 2: Quote Generation
```
Input: Lead ID + scope items
Expected:
  - Quote generated with itemized costs
  - Materials: $$
  - Labor: $$
  - Markup: $$
  - Total: $$
```

### Test 3: Follow-up
```
Input: Quote sent 3 days ago
Expected:
  - Friendly reminder generated
  - No corporate speak
  - <60 words
  - Call to action
```

### Test 4: Site Visit to Actions
```
Input: Voice memo transcription
Expected:
  - Materials list created
  - Subcontractors identified
  - Client promises captured
  - Action items created with priority
```

---

## 🚀 DEPLOYMENT ROADMAP

**Week 1**:
- ✅ Database schema
- ✅ Lead management API
- ✅ Quote generation API
- ✅ Basic dashboard UI

**Week 2**:
- ✅ Lead-to-Scope extractor integration
- ✅ Tradie persona follow-ups
- ✅ File management
- ✅ Advanced dashboard

**Week 3+**:
- ⏳ Payment tracking
- ⏳ Reporting/Analytics
- ⏳ Mobile app
- ⏳ Accounting integration

---

## ✅ VERIFICATION CHECKLIST

### For Each Feature
- [ ] Database table created
- [ ] API endpoint implemented
- [ ] Error handling added
- [ ] Test data available
- [ ] Dashboard section added
- [ ] Documentation updated
- [ ] User can complete workflow end-to-end

### For Lead Management
- [ ] Leads table exists
- [ ] GET/POST/PATCH endpoints work
- [ ] Lead extraction working
- [ ] Dashboard shows recent leads
- [ ] Can click to view details

### For Quote Pipeline
- [ ] Quotes table exists
- [ ] Quote generation working
- [ ] Status tracking working
- [ ] Pipeline dashboard shows summary
- [ ] Can update quote status

### For Files
- [ ] Files upload working
- [ ] Files linked to quotes
- [ ] File browser working
- [ ] Can preview/download files

### For AI Features
- [ ] Lead extraction prompt working
- [ ] Tradie persona follow-ups working
- [ ] Drafts show in UI
- [ ] Can edit and send

---

## 📞 NEXT STEPS

1. **Confirm Requirements**: Does this match what you need?
2. **Database Setup**: Create tables
3. **API Implementation**: Build endpoints
4. **UI Integration**: Add dashboard sections
5. **AI Integration**: Connect prompts
6. **Testing**: Verify end-to-end
7. **Deployment**: Go live

Ready to build this out? Let me know which module to start with! 🚀
