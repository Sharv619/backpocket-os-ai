# Twin Capabilities & Tools

## Current Tools Available to Twin

### 1. Email Services (services/gmail.py)
- **get_unread_emails()** - Fetch unread emails
- **send_email()** - Send emails
- **archive_message()** - Archive emails
- **get_historical_context()** - Get past emails from sender

### 2. AI Services (services/gemini.py)
- **triage_email()** - Categorize emails (Tier 1-5)
- **draft_response()** - Generate email drafts
- **refine_draft()** - Improve drafts based on feedback
- **batch_triage_emails()** - Bulk triage
- **get_ollama_response()** - Local AI (free, private)

### 3. Google Sheets (services/google_sheets.py)
- **add_new_client_to_master()** - Add client to Clients_Master
- **log_activity()** - Log to Sheets
- **check_client_identity()** - Lookup client
- **sync_instructions_to_sheets()** - Sync Twin instructions

### 4. WhatsApp (services/whapi.py)
- **send_whatsapp_message()** - Send notifications
- **send_notification()** - Send with buttons

### 5. Database (services/database.py)
- **save_sender_instruction()** - Save instructions
- **get_sender_instruction()** - Get instructions for sender
- **save_correction()** - Save corrections
- **get_corrections()** - Get past corrections

---

## Current AI Models

### Primary: Gemini (Cloud)
- **gemini-2.5-flash** - Fast, cheap
- **gemini-2.0-flash** - Fallback
- **Cost:** ~$0.01/email

### Fallback: Ollama (Local)
- **llama3.2** - Free, private
- **deepseek-r1:1.5b** - Reasoning
- **Cost:** FREE

---

## Twin Instructions System

### How Instructions Work:

1. **Save Instructions** (Twin Brain)
   ```
   Sender: jco064690@gmail.com
   Category: builder
   Instructions: "This is my builder. Add to Builder_Tracker, compare quotes..."
   ```

2. **Storage**
   - Local: SQLite `sender_instructions` table
   - Cloud: Google Sheets `Twin_Instructions` tab
   - Synced automatically

3. **Retrieval**
   - When email arrives → lookup sender
   - Include instructions in AI prompt
   - Use for drafting AND chat

---

## Self-Check System (To Prevent Hallucinations)

### Before Any Action, Twin MUST:
1. **Verify facts** - Don't assume, check with user
2. **Show reasoning** - Explain what it's doing
3. **Ask confirmation** - Never act without approval
4. **Flag uncertainties** - Say "I'm not sure" when needed
5. **Use tools properly** - Don't hallucinate API calls

### Hallucination Prevention Rules:
- Only use documented tools
- If tool not available, say "I don't have that capability"
- Always cite sources
- Admit when wrong

---

## Human-in-Loop Principle

**Nothing happens without approval:**
- Email → Draft → Chat → Approve → Send
- Client add → Review → Confirm → Add
- Any external action → Human must approve

---

## Version
Updated: March 29, 2026
