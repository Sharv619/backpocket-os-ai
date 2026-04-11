# BackPocket OS - API Reference

## Base URL

```
http://127.0.0.1:8000
```

---

## Health & Status

### Get Health Status

```http
GET /health
```

Response:
```json
{
  "status": "ok",
  "timestamp": "2026-04-12T03:00:00Z"
}
```

---

## Pending Approvals

### Get All Pending Approvals

Fetch all emails awaiting approval/response.

```http
GET /api/pending
```

Response:
```json
[
  {
    "ref_id": "DEMO-00001",
    "message_id": "msg_123",
    "thread_id": "thread_456",
    "sender": "steve.johnson@sparkypro.com.au",
    "subject": "Need a quote for rewire in Campbelltown",
    "delivered_to": "steve@backpocket.os",
    "snippet": "Hi Steve, Thanks for reaching out...",
    "draft_body": "Hi Steve,\n\nThank you for reaching out...",
    "tier": "1",
    "status": "pending",
    "timestamp": "2026-04-12T02:30:00Z"
  },
  ...
]
```

**Status codes:**
- `200` - Success
- `500` - Database error

---

## Approvals & Actions

### Approve an Email

Mark an email as approved (removes from pending queue).

```http
POST /api/approve
Content-Type: application/json

{
  "ref_id": "DEMO-00001"
}
```

Response:
```json
{
  "status": "approved",
  "ref_id": "DEMO-00001",
  "message": "Email approved and moved to history"
}
```

---

## Draft Management

### Save a Draft

Save or update a draft response.

```http
POST /api/save-draft
Content-Type: application/json

{
  "ref_id": "DEMO-00002",
  "draft_body": "Hi Mike,\n\nThank you for your message. I will review and respond shortly.\n\nBest regards, Steve"
}
```

Response:
```json
{
  "status": "saved",
  "ref_id": "DEMO-00002",
  "updated_at": "2026-04-12T03:15:00Z"
}
```

### Get All Drafts

Retrieve all saved drafts.

```http
GET /api/drafts
```

Response:
```json
[
  {
    "ref_id": "DEMO-00001",
    "draft_body": "Hi Steve,\n\nThank you...",
    "updated_at": "2026-04-12T02:45:00Z",
    "status": "pending_review"
  },
  ...
]
```

### Get Specific Draft

Retrieve a single draft by reference ID.

```http
GET /api/draft/{ref_id}
```

Example:
```http
GET /api/draft/DEMO-00001
```

Response:
```json
{
  "ref_id": "DEMO-00001",
  "draft_body": "Hi Steve,\n\nThank you for reaching out...",
  "updated_at": "2026-04-12T02:45:00Z",
  "status": "pending_review"
}
```

---

## Documents

### Upload Document

Upload a document (PDF, image, etc.) for analysis.

```http
POST /api/documents/upload
Content-Type: multipart/form-data

file: <binary file>
document_type: "invoice|receipt|contract|other"
```

Response:
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "invoice_123.pdf",
  "document_type": "invoice",
  "status": "uploaded",
  "created_at": "2026-04-12T03:20:00Z",
  "size_bytes": 45678
}
```

### List All Documents

Get all uploaded documents.

```http
GET /api/documents
```

Response:
```json
[
  {
    "document_id": "550e8400-...",
    "filename": "invoice_123.pdf",
    "document_type": "invoice",
    "status": "uploaded",
    "created_at": "2026-04-12T03:20:00Z"
  },
  ...
]
```

### Get Document Details

Retrieve metadata for a specific document.

```http
GET /api/documents/{doc_id}
```

Response:
```json
{
  "document_id": "550e8400-...",
  "filename": "invoice_123.pdf",
  "document_type": "invoice",
  "status": "analyzed",
  "created_at": "2026-04-12T03:20:00Z",
  "analysis": "Invoice from Bunnings Business. Amount: $450.00. Date: 2026-04-10.",
  "extracted_fields": {
    "invoice_number": "BT-8821",
    "supplier": "Bunnings Business",
    "amount": "$450.00",
    "date": "2026-04-10"
  }
}
```

### Analyze Document

Run vision AI (Moondream) analysis on uploaded document.

```http
POST /api/documents/analyze/{doc_id}
```

Response:
```json
{
  "document_id": "550e8400-...",
  "status": "analyzing",
  "message": "Analysis started. Check back in 30 seconds."
}
```

**Note**: Analysis is asynchronous. Polling the endpoint will eventually return full results.

### Delete Document

Remove a document.

```http
DELETE /api/documents/{doc_id}
```

Response:
```json
{
  "status": "deleted",
  "document_id": "550e8400-..."
}
```

---

## Twin Brain Chat

### Send Message to Twin

Chat with AI assistant about pending work.

```http
POST /api/twin-chat
Content-Type: application/json

{
  "message": "How many urgent emails do I have?",
  "conversation_id": "default"
}
```

Response:
```json
{
  "response": "You have 2 tier-1 urgent emails: one from Steve Johnson about a quote, and one from Mike Walsh about an invoice. Both need responses within today.",
  "conversation_id": "default",
  "timestamp": "2026-04-12T03:25:00Z"
}
```

---

## Gmail Integration

### Search Gmail

Search inbox using Gmail query syntax.

```http
POST /api/search-gmail
Content-Type: application/json

{
  "q": "from:steve.johnson@sparkypro.com.au"
}
```

Response:
```json
[
  {
    "message_id": "msg_789",
    "sender": "steve.johnson@sparkypro.com.au",
    "subject": "Need a quote for rewire in Campbelltown",
    "snippet": "Hi Steve, Thanks for reaching out...",
    "timestamp": "2026-04-12T02:30:00Z"
  },
  ...
]
```

**Query Examples:**
- `"from:email@domain.com"` — from specific sender
- `"subject:invoice"` — in subject line
- `"after:2026-04-01"` — after a date
- `"label:important"` — in label
- `"is:unread"` — unread only
- `"in:inbox"` — in inbox only

---

## Sender Instructions

### Get Sender Instructions

Retrieve handling instructions for a specific sender.

```http
GET /api/sender-instruction/{sender_email}
```

Example:
```http
GET /api/sender-instruction/steve.johnson@sparkypro.com.au
```

Response:
```json
{
  "sender_email": "steve.johnson@sparkypro.com.au",
  "instructions": "Always respond within 4 hours. Keep responses brief.",
  "tier_override": null,
  "tags": ["tradie", "vip"]
}
```

---

## Conversations

### Get All Conversations

List all chat conversations with AI.

```http
GET /api/conversations
```

Response:
```json
[
  {
    "conversation_id": "conv_001",
    "title": "Monday Pending Review",
    "created_at": "2026-04-12T02:00:00Z",
    "message_count": 5,
    "last_message_at": "2026-04-12T02:45:00Z"
  },
  ...
]
```

### Get Conversation Messages

Retrieve all messages in a conversation.

```http
GET /api/conversations/{conversation_id}
```

Response:
```json
{
  "conversation_id": "conv_001",
  "title": "Monday Pending Review",
  "messages": [
    {
      "role": "user",
      "message": "What are my priorities today?",
      "timestamp": "2026-04-12T02:00:00Z"
    },
    {
      "role": "assistant",
      "message": "Based on your pending approvals, you have 2 tier-1 items...",
      "timestamp": "2026-04-12T02:01:00Z"
    }
  ]
}
```

### Get Recent Messages

Get last N messages from a conversation.

```http
GET /api/conversations/{conversation_id}/recent?limit=10
```

### Delete Conversation

Remove a conversation.

```http
DELETE /api/conversations/{conversation_id}
```

---

## Mobile API Endpoints

These simplified endpoints are optimized for mobile apps (Flutter, etc.).

### Get Mobile Pending

Simplified pending approvals for mobile.

```http
GET /api/mobile/pending
Header: X-API-Key: <BP_API_KEY from .env>
```

Response:
```json
[
  {
    "ref_id": "DEMO-00001",
    "tier_label": "🔴 Urgent",
    "preview": "Steve Johnson: Need a quote for rewire...",
    "age_hours": 2
  },
  ...
]
```

### Mobile Approve

Quick approve from mobile.

```http
POST /api/mobile/approve
Header: X-API-Key: <BP_API_KEY from .env>
Content-Type: application/json

{
  "ref_id": "DEMO-00001",
  "note": "Approved - will contact client"
}
```

### Mobile Chat

Lightweight chat endpoint for mobile.

```http
POST /api/mobile/chat
Header: X-API-Key: <BP_API_KEY from .env>
Content-Type: application/json

{
  "message": "What's next?"
}
```

---

## Error Responses

All errors return appropriate HTTP status codes with details:

```json
{
  "error": "Email not found",
  "detail": "ref_id DEMO-99999 does not exist",
  "status_code": 404
}
```

Common codes:
- `200` - Success
- `201` - Created
- `400` - Bad request (invalid JSON/params)
- `401` - Unauthorized (missing API key for protected endpoints)
- `404` - Not found
- `500` - Server error (database issue, etc.)

---

## Authentication

Most endpoints work without authentication. Protected endpoints require `X-API-Key` header:

```bash
curl -H "X-API-Key: YOUR_BP_API_KEY" http://127.0.0.1:8000/api/mobile/pending
```

Get `BP_API_KEY` from `.env` file (or set a strong random value).

---

## Rate Limits

No rate limiting implemented in local mode. In production:
- Gemini API: ~60 requests/minute
- Gmail API: ~100 requests/minute
- Local document analysis: Limited by Ollama processing speed

---

## Examples

### Complete Workflow

```bash
# 1. Get pending
curl -s http://127.0.0.1:8000/api/pending | jq '.[] | {ref_id, sender, tier}'

# 2. Review a draft
curl -s http://127.0.0.1:8000/api/draft/DEMO-00001 | jq .draft_body

# 3. Edit draft
curl -X POST http://127.0.0.1:8000/api/save-draft \
  -H "Content-Type: application/json" \
  -d '{
    "ref_id": "DEMO-00001",
    "draft_body": "Hi Steve, Thanks for the inquiry. Let me get back to you shortly."
  }'

# 4. Approve
curl -X POST http://127.0.0.1:8000/api/approve \
  -H "Content-Type: application/json" \
  -d '{"ref_id": "DEMO-00001"}'

# 5. Verify removed from pending
curl -s http://127.0.0.1:8000/api/pending | jq 'length'
```

### Document Processing

```bash
# 1. Upload
curl -X POST http://127.0.0.1:8000/api/documents/upload \
  -F "file=@invoice.pdf" \
  -F "document_type=invoice"

# 2. Analyze
curl -X POST http://127.0.0.1:8000/api/documents/analyze/550e8400-...

# 3. Check results
curl -s http://127.0.0.1:8000/api/documents/550e8400-... | jq .extracted_fields
```

---

## Dashboard Access

The web dashboard is at:

```
http://127.0.0.1:8000/static/index.html
```

No authentication required. Provides UI for all major operations.
