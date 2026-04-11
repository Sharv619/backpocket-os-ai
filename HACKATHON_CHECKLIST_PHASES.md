# 🏁 BackPocket OS: Hackathon Checklist
*Based on the WSTI AI Hackathon 6-Phase Cheatsheet*

## PHASE 1: THE PROBLEM (Sat 9:00 AM)
- [x] One Sentence: "Sole traders in Western Sydney struggle with admin-drowning because they have no affordable technical staff."
- [x] Target User: Steve the Western Sydney Tradie.
- [x] Workaround: 11:00 PM laptop sessions at the kitchen table.

## PHASE 2: DESIGN (Sat 11:00 AM)
- [x] Core 3 Features: 
    1. AI Triage.
    2. WhatsApp Approvals.
    3. Document Research.
- [x] **"WOW" Moment**: Email -> WhatsApp notification loop under 10 seconds.
- [x] Tech Stack: FastAPI, Gemini 2.5-flash, WhatsApp API, SQLite.

## PHASE 3: TEAM ROLES (Assigned)
- [x] Team Lead: Cherry
- [x] Lead Builder (Backend & Frontend Wiring): Himanshu
- [x] Pitcher/Marketer: Echo
- [x] Domain Expert/IT: Allan
- [x] The "Digital" Employee: Pip (The AI Twin)

## PHASE 4: THE BUILD (Sat 1:00 PM - Sun 1:00 PM)
- [ ] **Technical**: End-to-end triages works for real emails.
- [ ] **UI**: Dashboard matches Magic Patterns design (Himanshu/Echo).
- [x] **Demo Mode**: 5 mock pending emails ready for demo
- [ ] **Bonus**: Landing page created with Bolt/Lovable.
- [ ] **Save**: Git Push every 60 minutes.

## PHASE 5: THE POLISH (Sun 2:00 PM)
- [ ] **FEATURE FREEZE** (2:00 PM Sharp). 
- [ ] Test the demo path 5 times on 5 different phones.
- [ ] Clear up any console errors in the frontend.

## PHASE 6: THE PITCH (Sun 3:30 PM & Beyond)
- [ ] Practice the "Steve Story."
- [ ] Finalize the 3-minute video recording (Due 26 Apr).
- [ ] Emphasize the $9 Billion Capacity Gap.

---

## 📊 Current Build Status (2026-04-11)

### ✅ Complete
- 5-tier triage logic in `services/gemini.py`
- WhatsApp commands (approve, revise, supplier, find, get)
- Database schema + mock data (5 sample emails) 
- Dashboard UI
- Twin instructions (20 rules)
- Docs organized into structured folders

### ❌ Needs API Keys
- Gmail API (credentials.json)
- Google Sheets (credentials.json)
- Gemini API key (.env)
- WhatsApp token (.env)
