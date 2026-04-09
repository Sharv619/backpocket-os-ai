# BackPocket OS - Journey Log

## Date: March 2026

### Current Status
- Version 2.2
- Running on Desktop for development
- 24/7 mini-pc deployment in progress

---

## Issues Encountered & Fixes

### 1. Charmap Encoding Error
**Problem:** `'charmap' codec can't encode character '\u2705'`
**Cause:** Windows console couldn't handle emojis
**Fix:** Added UTF-8 encoding at top of all Python files

### 2. Dashboard Not Loading
**Problem:** Closing terminal stopped server
**Fix:** Need auto-start for 24/7 (SETUP_AUTOSTART.bat)

### 3. Pending Emails Not Showing
**Problem:** Clicking "Pending Approvals" showed blank screen
**Fix:** Changed to `showEmailTab('pending')` instead of `showSection`

### 4. Revision Not Being Used
**Problem:** Revised drafts weren't sent, original was sent
**Fix:** 
- Added corrections to database
- Added `sender_instructions` table for Twin learning
- AI now reads corrections when drafting

### 5. Google Sheets Link Not Working
**Problem:** URL not showing
**Fix:** Added debug endpoint to check SPREADSHEET_ID loading

### 6. Logo Not Clickable
**Problem:** Couldn't go back to home
**Fix:** Added onclick to logo header

---

## Features Implemented

### Tier Rules (Updated March 29, 2026)
- Tier 1: Existing clients (stay in inbox, needs draft)
- Tier 2: Govt/Assoc (ATO, ASIC) - stay in inbox, log only
- Tier 3: Suppliers - log to Supplier_Expenses sheet, STAY IN INBOX
- Tier 4: Portal Digests - log to Activity_Log + Portal_Updates, then archive
- Tier 5: Spam - log to SPAM sheet and archive

### Twin Learning & Smart Actions
- Corrections saved to database
- Sender-specific instructions in Twin Brain
- Instructions synced to Google Sheets (Twin_Instructions tab)
- AI reads context when drafting
- **Suggested Actions** - Twin suggests actions based on sender instructions
- **HUMAN IN THE LOOP** - All external actions require approval

### Human-in-Loop Principle
**Nothing goes out without human approval:**
- ✅ Email drafts → Pending → Human approves → Sends
- ✅ Suggested actions → Displayed → Human approves → Executes
- ✅ Client additions → Human reviews → Added to Sheets
- ✅ Any external communication → Must be approved

### How Twin Brain Works
1. Email arrives → Twin checks sender instructions
2. Draft generated → Includes sender-specific guidance
3. Suggested actions displayed → Human reviews
4. Human clicks "Approve" → Action executes

---

## Current Architecture

```
Email → Twin AI → Draft + Suggestions → Human Approval → Action
         ↑
    Sender Instructions
    (Twin Brain)
```

### Twin Learning
- Corrections saved to database
- Sender-specific instructions
- AI reads context when drafting

### Dashboard
- Stats boxes clickable
- Back navigation on all sections
- Twin Brain section for instructions

---

## Current Known Issues
1. Revision sometimes doesn't save properly
2. Chat feature needs more functionality
3. Need to test on mini-pc with Ollama
