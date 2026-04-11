# MCP Orchestrator: BackPocket's Intelligent AI Coordination System

## Overview

The **Model Context Protocol (MCP)** turns BackPocket into a high-powered orchestrator that connects:
- **Gmail MCP** → Email & communication
- **Google Drive MCP** → File organization
- **Google Maps MCP** → Location & routing  
- **BackPocket Local MCP** → Database & tradie business logic

Instead of custom API boilerplate, MCP provides a standardized way for your AI to "reach out" and touch the data.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Claude AI (or any LLM)                      │
└────────────────┬────────────────────────────────────────────────┘
                 │ (Uses MCP Tools)
      ┌──────────┴──────────┬─────────────────┬──────────────────┐
      │                     │                 │                  │
  ┌───▼────┐          ┌────▼──┐         ┌───▼────┐         ┌───▼─────┐
  │ Gmail  │          │Google │         │ Google │         │BackPocket│
  │  MCP   │          │ Drive │         │ Maps   │         │ Local MCP│
  │        │          │ MCP   │         │ MCP    │         │          │
  └───┬────┘          └────┬──┘         └───┬────┘         └───┬──────┘
      │                    │                │                  │
  ┌───▼────────────────────▼────────────────▼──────────────────▼─────┐
  │                    DATA INTEGRATION LAYER                         │
  │  • Gmail (search, draft, send)                                    │
  │  • Google Drive (list, read, organize)                           │
  │  • Google Maps (distance, routing, time)                         │
  │  • SQLite (leads, quotes, payments)                              │
  │  • ChromaDB (learned patterns)                                   │
  └─────────────────────────────────────────────────────────────────┘
```

---

## Setup Instructions

### 1. Install MCP Configuration

Copy `.mcp.json` to your Claude Desktop config or project root:

```bash
# For Claude Desktop (macOS)
cp .mcp.json ~/.claude/config.json

# For project-level development
# .mcp.json is already in repo root
```

### 2. Install BackPocket Local MCP Server

```bash
cd src/mcp-wrapper
npm install
chmod +x server.js
```

### 3. Set Environment Variables

Add to your `.env`:

```bash
# Gmail MCP
GMAIL_CLIENT_ID=your_client_id_from_google_cloud
GMAIL_CLIENT_SECRET=your_client_secret

# Google Maps MCP
GOOGLE_MAPS_API_KEY=your_maps_api_key

# BackPocket Local MCP
LOCAL_DB_PATH=./backpocket.db
CHROMADB_PATH=./chromadb
```

### 4. Verify MCP Servers are Accessible

```bash
# Test Gmail MCP
npx -y @modelcontextprotocol/server-gmail list

# Test Google Drive MCP
npx -y @modelcontextprotocol/server-google-drive list

# Test BackPocket Local MCP
node src/mcp-wrapper/server.js
```

---

## BackPocket Local MCP Tools

### Lead Management

#### `search_leads`
Find construction leads with filters.

**Parameters:**
- `status`: 'new', 'quoted', 'accepted'
- `job_type`: 'Kitchen', 'Plumbing', 'Deck', etc.
- `urgency`: 'high', 'medium', 'low'
- `min_budget`: Minimum budget amount
- `location`: Suburb or area

**Example:**
```json
{
  "tool": "search_leads",
  "params": {
    "status": "new",
    "urgency": "high",
    "min_budget": 10000
  }
}
```

**Response:**
```json
{
  "count": 3,
  "leads": [
    {
      "id": 1,
      "client_name": "Sarah Mitchell",
      "job_type": "Kitchen Renovation",
      "location": "Parramatta",
      "urgency": "high",
      "estimated_budget": 15000
    }
  ]
}
```

---

### Quote Generation

#### `create_quote`
Generate a quote with tradie pricing ($150/hr base rate).

**Parameters:**
- `lead_id`: Lead to quote for
- `materials_cost`: Material costs
- `labor_hours`: Hours of labor
- `markup_percent`: Markup % (default 20%)

**Example:**
```json
{
  "tool": "create_quote",
  "params": {
    "lead_id": 1,
    "materials_cost": 8000,
    "labor_hours": 5,
    "markup_percent": 20
  }
}
```

**Response:**
```json
{
  "quote_id": 42,
  "materials": 8000,
  "labor": 750,
  "subtotal": 8750,
  "markup_percent": 20,
  "total_amount": 10500
}
```

#### `get_quote_template`
Get pricing templates for different job types.

**Example:**
```json
{
  "tool": "get_quote_template",
  "params": {
    "job_type": "Kitchen"
  }
}
```

**Response:**
```json
{
  "job_type": "Kitchen",
  "labor_rate": "150/hour",
  "materials_markup": "30%",
  "estimated_duration": "5 hours"
}
```

---

### Pipeline & Payments

#### `get_pipeline_summary`
Current quote pipeline status.

**Response:**
```json
{
  "total_quotes": 12,
  "draft": 3,
  "sent": 4,
  "accepted": 5,
  "revenue_pipeline": 52000
}
```

#### `record_payment`
Log a payment received.

**Parameters:**
- `quote_id`: Quote being paid
- `amount`: Amount received
- `payment_date`: (optional) Payment date

#### `get_overdue_quotes`
Quotes sent but not accepted (past 7 days).

**Example:**
```json
{
  "tool": "get_overdue_quotes",
  "params": {
    "days_threshold": 7
  }
}
```

**Response:**
```json
{
  "count": 2,
  "overdue_quotes": [
    {
      "id": 5,
      "client_name": "John Smith",
      "job_type": "Plumbing",
      "total_amount": 2800,
      "sent_date": "2026-04-05"
    }
  ],
  "message": "2 quotes overdue - consider follow-up"
}
```

---

### Location & Routing (Google Maps Integration)

#### `calculate_job_distance`
Distance from home base to job location.

**Parameters:**
- `from_location`: Start (e.g., 'Alexandria')
- `to_location`: Job location
- `traffic`: Include traffic (optional)

**Response:**
```json
{
  "distance_km": 15.3,
  "estimated_travel_time": "25 minutes",
  "note": "Use Google Maps MCP for real calculation"
}
```

#### `estimate_travel_time`
Suggest calendar block including travel buffer.

**Parameters:**
- `job_location`: Job address
- `job_duration_hours`: Job duration
- `include_buffer`: Add 30min before/after

**Response:**
```json
{
  "job_location": "123 Main St, Penrith",
  "job_duration": "3 hours",
  "travel_buffer": "1 hours (30min before, 30min after)",
  "total_calendar_block": "4 hours",
  "suggested_time_slot": "Morning (8am) or Afternoon (1pm)"
}
```

---

### Learned Patterns

#### `get_job_patterns`
Historical patterns for a job type.

**Parameters:**
- `job_type`: Job type
- `location`: Suburb (optional)

**Response:**
```json
{
  "job_type": "Kitchen",
  "avg_price": 8500,
  "avg_duration": 5,
  "materials_percentage": 40,
  "common_issues": ["Cabinet alignment", "Plumbing conflicts", "Electrical upgrades"],
  "repeat_rate": 0.65,
  "note": "Based on historical data"
}
```

#### `get_client_history`
Past jobs, preferred communication, repeat patterns.

**Parameters:**
- `client_email`: Client email address

**Response:**
```json
{
  "client_email": "john@example.com",
  "total_jobs": 3,
  "repeat_customer": true,
  "preferred_contact": "SMS",
  "avg_job_value": 5000,
  "last_job_date": "2026-03-15"
}
```

---

### Communication (Gmail Integration)

#### `draft_follow_up_email`
Generate follow-up message template.

**Parameters:**
- `quote_id`: Quote to follow up on
- `tone`: 'friendly', 'professional', 'urgent'

**Response:**
```json
{
  "quote_id": 1,
  "tone": "friendly",
  "email_body": "Hi, just checking in on the quote I sent over...",
  "subject_suggestion": "Follow-up: Your Quote from BackPocket",
  "action": "Ready to send via Gmail MCP"
}
```

#### `match_quote_to_email`
Match incoming email to a quote (auto follow-up).

**Parameters:**
- `email_from`: Sender email
- `email_subject`: Subject
- `email_body`: Body

**Response:**
```json
{
  "status": "analysis_complete",
  "matched_quote_ids": [1, 2],
  "confidence": 0.85,
  "suggested_action": "Send follow-up or update quote status"
}
```

---

### AI Decision Making

#### `suggest_next_action`
AI suggests next step based on context.

**Parameters:**
- `context`: 'new_lead', 'quote_sent', 'quote_accepted', 'payment_received'

**Response:**
```json
{
  "context": "quote_sent",
  "suggested_action": "Follow up in 5 days if no response",
  "next_steps": ["Update CRM", "Calendar block", "Send communication"]
}
```

---

## Real-World Workflow Example: "Accept Job & Send Quote"

**Scenario:** Email arrives: "Leaking tap in Parramatta, need ASAP, budget $200"

### Step 1: Gmail MCP finds email
```json
{
  "tool": "gmail/search_emails",
  "query": "leaking tap"
}
```

### Step 2: BackPocket Local MCP extracts lead
```json
{
  "tool": "search_leads",
  "params": {
    "job_type": "Plumbing",
    "location": "Parramatta",
    "urgency": "high"
  }
}
```

### Step 3: Get pricing template
```json
{
  "tool": "get_quote_template",
  "params": {
    "job_type": "Plumbing"
  }
}
```
Response: `$150/hr, materials +20%`

### Step 4: Estimate distance via Google Maps MCP
```json
{
  "tool": "calculate_job_distance",
  "params": {
    "from_location": "Alexandria (home base)",
    "to_location": "Parramatta"
  }
}
```
Response: `25 minutes, 15.3km`

### Step 5: Create quote
```json
{
  "tool": "create_quote",
  "params": {
    "lead_id": 42,
    "materials_cost": 120,
    "labor_hours": 1.5,
    "markup_percent": 20
  }
}
```
Response: `Quote #99: $414 total` ✅

### Step 6: Draft follow-up
```json
{
  "tool": "draft_follow_up_email",
  "params": {
    "quote_id": 99,
    "tone": "friendly"
  }
}
```

### Step 7: Send via Gmail MCP
```json
{
  "tool": "gmail/send_message",
  "params": {
    "to": "customer@example.com",
    "subject": "Quick Fix: Leaking Tap - $414",
    "body": "Hi, can fix that leaking tap...",
    "draft_id": 99
  }
}
```

### **Result:** Single button presented to user:
```
✅ Accept Job & Send Quote ($414)?
   • Distance: 25 min from base
   • Time slot: 10am-11:30am
   • Materials: $120 | Labor: $225 (1.5hrs)
   • Margin: $69 (20%)
```

---

## Integration with Other Services

### Gmail MCP Tools
- `search_emails` - Find emails by criteria
- `list_messages` - List inbox
- `create_draft` - Draft a message
- `send_message` - Send email
- `list_attachments` - Get file attachments
- `forward_message` - Forward email

### Google Drive MCP Tools
- `list_files` - List documents
- `create_file` - Upload document
- `read_file` - Read file content
- `share_file` - Share with client
- `organize_by_job` - Organize files by job ID

### Google Maps MCP Tools
- `distance_matrix` - Distances between locations
- `directions` - Route optimization
- `geocode` - Address lookup
- `time_zone` - Client timezone

---

## Best Practices

### 1. **Cache Results**
Don't refetch quote templates or historical patterns on every request.

```python
# Cache job patterns in memory
cache = {}
if 'Kitchen' not in cache:
    cache['Kitchen'] = get_job_patterns('Kitchen')
template = cache['Kitchen']
```

### 2. **Combine Tools**
Link multiple MCP tools for intelligent decisions.

```python
# Workflow: Email → Lead → Quote → Send
email_data = gmail_mcp.search_emails("emergency leak")
lead = extract_lead_from_email(email_data)
quote = create_quote_with_template(lead)
distance = maps_mcp.distance(home_base, lead.location)
send_quote_with_routing_info(quote, distance)
```

### 3. **Fallback Gracefully**
If Google Maps MCP is down, estimate travel time with fallback.

```python
try:
    distance = maps_mcp.distance(from_loc, to_loc)
except:
    distance = estimated_distance_by_suburb(from_loc, to_loc)
```

### 4. **Log All Decisions**
Store which MCP tools were used for audit trail.

```python
decision_log = {
    "timestamp": "2026-04-12T10:30:00Z",
    "tools_used": ["search_leads", "get_quote_template", "create_quote"],
    "decision": "Accept job & send quote",
    "confidence": 0.95
}
```

---

## Troubleshooting

### MCP Server Won't Start
```bash
# Check Node.js version
node --version  # Should be >=18.0.0

# Test database connection
sqlite3 ./backpocket.db "SELECT COUNT(*) FROM leads;"

# Check file permissions
chmod +x src/mcp-wrapper/server.js
```

### Gmail MCP Not Authenticating
```bash
# Verify credentials in .env
echo $GMAIL_CLIENT_ID
echo $GMAIL_CLIENT_SECRET

# Re-authenticate
npx -y @modelcontextprotocol/server-gmail auth
```

### Google Maps Distance Returning Zeros
```bash
# Check API key
echo $GOOGLE_MAPS_API_KEY

# Verify API is enabled in Google Cloud Console
# Maps Distance Matrix API should be enabled
```

---

## Future Enhancements

1. **Semantic Search via ChromaDB MCP** - Find similar past jobs
2. **Calendar MCP** - Auto-block travel time when quote accepted
3. **Slack MCP** - Send notifications to team
4. **Stripe MCP** - Process payments automatically
5. **Document OCR MCP** - Extract data from invoices/receipts

---

## References

- [MCP Protocol Spec](https://modelcontextprotocol.io/)
- [Official MCP Servers](https://github.com/modelcontextprotocol/servers)
- [Gmail MCP Server](https://github.com/modelcontextprotocol/servers/tree/main/src/gmail)
- [Google Drive MCP Server](https://github.com/modelcontextprotocol/servers/tree/main/src/google-drive)

---

**Last Updated:** April 12, 2026  
**Status:** ✅ MCP Orchestrator Ready for Claude Code Integration
