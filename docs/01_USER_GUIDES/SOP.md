# 📖 BackPocket Twin: The Easy-Peasy Manual (SOP) 🍒🤖

> **Current Version:** 3.0 (Updated 2026-03-30)
> **Status:** Active - Email triage, Document processing, AI Agents

Hello! This is the book of rules for your **BackPocket Twin**. We wrote this so it's easy to understand, even for a five-year-old! 👧👦

---

## ⚡ QUICK START

1. **Start Twin**: Run `LAUNCH_BACKPOCKET_TWIN.bat`
2. **Open Dashboard**: http://localhost:8000/dashboard
3. **Check WhatsApp**: Approve emails with `approve <ref>`

---

## 🏗️ 1. What is the Twin?
The Twin is like a **smart robot assistant** that lives in your computer.
- It **hears** when people email you.
- It **thinks** about what they want.
- It **writes** a nice reply for you.
- It **waits** for you to say "Yes" on WhatsApp before it sends anything.

---

## 🚦 2. The "Stoplight" Rules (Triage)
The Twin looks at every email and puts it in a colored box:
1.  🔴 **Tier 1 (Priority)**: Super important! These are clients who need help NOW.
    - *Action*: Twin sends you a WhatsApp right away.
2.  🟡 **Tier 2 (Sales)**: New friends!
    - *Action*: If they are in our **Master List**, Twin writes a draft. If they are NEW, Twin asks you: *"Is this a Lead or a Supplier?"*
3.  🟢 **Tier 3 (General)**: Just asking questions.
    - *Action*: Twin writes a professional note using your **Background Info** from the sheet.
4.  ⚪ **Tier 4 (Updates)**: Just news or "Thank you" notes.
    - *Action*: Twin files them in `Portal_Updates`. **IMPORTANT**: If the sender is a client, the Twin will STILL send you a WhatsApp nudge so you don't miss anything (The "Rowan Rule").
5.  🚮 **Tier 5 (Spam)**: JUNK!
    - *Action*: Twin throws these in the `Spam_Archive`.

---

## 🧠 3. The "Free Brain" Strategy (Cost Savings)
Your Twin is now super smart about how it spends money:
- **Rule-Based Filters**: Twin has a local "Pre-Filter" that catches simple spam and polite noise ("thanks!", "got it") without asking an AI. This is **100% Free**.
- **Batch Processing**: Instead of asking Gemini for help 10 times for 10 emails, Twin gathers them all and asks just **once**. This saves 80-90% of your API quota.
- **Local Fallback (Ollama)**: If the cloud (Gemini) says "I'm too busy" or "Too many requests," your **Mini-PC** automatically takes over. It uses a local AI engine called **Ollama** so the work never stops.

---

## 📱 3. How to Talk to your Twin (WhatsApp)
The Twin will send you a message like this: 
> "🤖 Ref #1234. AI Draft: Hi, I can help you with your tax!"

**You have 4 magic commands:**
1.  ✅ **`approve 1234`**: You are telling the Twin: *"Great job! Send that email now!"*
2.  🔄 **`revise 1234: make it shorter`**: You are telling the Twin: *"Almost there, but fix it like this."*
3.  🚚 **`supplier 1234`**: You are telling the Twin: *"Actually, this is a bill/supplier. Move it to the Supplier_Expenses sheet."*
4.  📋 **`approve`**: You are asking: *"What else is waiting for me to check?"*

---

## 🎭 4. The "Magic Hats" (Brand Names)
You have many business names (like *Your Web Accountant* or *Big Boss*). 
- The Twin is a master of disguise! 
- It looks at who the client emailed.
- It puts on the **correct hat**.
- The client always sees the right name and email in the reply.

---

## 🕹️ 5. The Control Center (Dashboard)
We have built a beautiful web interface so you don't have to use a terminal or know any code.
- **Where to go**: Open your browser and go to `http://localhost:8000/dashboard`.
- **The "Rescue" Tab**: If an email is missing, just type the name or a keyword. The Twin will show you all matches from the archives and trash. Just click **⚓ Rescue to Inbox**, and it will put it back exactly where it belongs.
- **The "Pending" Tab**: See all the emails that are currently waiting for your WhatsApp approval.

---

## 🛠️ 6. What if the Twin stops working?
If the Twin isn't talking to you:
1.  **Check the Command Center**: Click the `COMMAND_CENTER.md` file in the brain folder.
2.  **Check Ngrok**: Make sure your "Secret Tunnel" is still open.
3.  **Check the Dashboard**: Refresh `http://localhost:8000/dashboard`. If it doesn't load, the "Twin" might be sleeping—just restart the `main.py` script.

---

## 📝 6. The Long-Term Memory
Every time you use the Twin, it writes it down in your Google Sheets: 
- **Clients_Master**: All your client names and background notes. The Twin reads this to know who it’s talking to!
- **Leads_Capture**: For new sales inquiries.
- **Supplier_Expenses**: For bills and invoices.
- **Action_Log**: A record of every single action the Twin took.
- **SQLite Database**: This is the Twin's "internal brain" that makes it super fast.

---

## 🤝 7. How We Work Together (The Assistant)
While we build your Twin, I (**Antigravity**) am your coding partner!
- **I can see your screen**: I can see where your cursor is and what code you are looking at.
- **I can hear your needs**: You don't have to explain everything perfectly—just point to a file, and I’ll know what to do!
- **I can build anything**: You are the pilot, and I am the super-fast helper building the robot parts!

---

---

## 🚨 8. The Emergency Handover (Switching AI)
This system is maintained by **OpenCode** (AI coding assistant). To continue development:
1. Run `opencode` in terminal - it reads SYSTEM_CONTEXT.md automatically
2. Or open **`docs/HANDOVER_SOP.md`** for full transition steps

---

## 📋 CURRENT FEATURES (v3.0)

| Feature | Status | How to Use |
|---------|--------|------------|
| Email Triage (5 tiers) | ✅ Active | Emails auto-triaged, WhatsApp approval |
| WhatsApp Commands | ✅ Active | `approve`, `revise`, `supplier`, `spam`, `find` |
| Document Processing | ✅ Active | Upload via Dashboard > Docs tab |
| AI Agents (5) | ✅ Active | Dashboard > Agents tab - Accountant, Auditor, Admin, Coach, Marketing |
| Twin Chat | ✅ Active | Dashboard > Home - knows system, accounting, automation |
| Dashboard | ✅ Active | http://localhost:8000/dashboard |

### AI Agents - What They Do:

| Agent | Skills | Future Tools |
|-------|--------|---------------|
| Senior Accountant | Bookkeeping, BAS, tax | Xero API, MYOB API (via MCP) |
| Senior Auditor | Reviews, compliance, anomalies | File access, spreadsheet analysis |
| Admin Assistant | Scheduling, notes, queries | Calendar, email integration |
| Communication Coach | Speaking practice | Yoodli integration |
| Marketing Specialist | Content, social media | Post scheduling, analytics |
4. They will be fully up to speed in seconds!

---

**Remember: You are the Boss! The Twin never sends an email until you say "Approve."** 🚀🍒
