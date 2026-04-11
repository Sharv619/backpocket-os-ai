# BackPocket OS — 3-Minute Demo Script
**Hackathon Presentation — Cherry leads, Himanshu on laptop**

---

## Setup (Before You Go On Stage)

```bash
# Terminal 1: Start the demo server
./START_DEMO.sh

# Verify these work:
# http://127.0.0.1:8000/static/index.html  ← open in browser
# http://127.0.0.1:8000/api/mobile/pending ← open in second tab
```

Make sure `.env` has `DEMO_MODE=1` so no real emails fire during the demo.

---

## The Script

### 0:00 — The Hook (Cherry speaks)

> "Meet Steve. He's a plumber in Western Sydney. Last week he missed a $4,800
> invoice because he was on a job site and couldn't check his emails for three days.
> That's the Shadow Week — and it costs Western Sydney businesses $9 billion a year.
> BackPocket fixes this."

*(Himanshu opens the dashboard: http://127.0.0.1:8000/static/index.html)*

---

### 0:30 — Show the Inbox (Himanshu demos)

> "This is Cherry's AI-powered inbox. Every email has been triaged and ranked
> by our Digital Twin — same logic Cherry uses, trained on her corrections."

Point to the screen:
- **[1] URGENT** — Steve's invoice overdue
- **[2] HIGH** — BAS lodgment question
- **[3-5]** — Telstra bill, Xero digest, spam

> "The AI already drafted replies for every Tier 1 and 2 email. Cherry just reviews."

---

### 1:00 — The One-Tap Approve (Live action)

> "Steve's invoice. Cherry reads the draft. Looks good. One tap."

*(Click "Approve" on DEMO-00001)*

> "Email sent. And because it's Tier 1..."

*(WhatsApp notification appears on Cherry's phone — or show the API response)*

> "...Steve gets a WhatsApp in under 3 seconds. Cherry never opened Gmail."

---

### 1:45 — Talk to Your Twin (Live chat)

*(Open the Twin Chat tab, type: "What needs attention today?")*

> "The Twin knows Cherry's business. It knows her clients, her tone,
> what she approved last week, what she revised. It learns."

*(Wait for response, read first line aloud)*

> "This isn't a chatbot. This is Cherry's second brain."

---

### 2:15 — The Mobile Angle (Himanshu opens second browser tab)

*(Open: http://127.0.0.1:8000/api/mobile/pending)*

> "Every one of these endpoints works from a Flutter mobile app.
> Cherry approves emails from her phone, on the go, between client meetings."

*(Show the JSON response — clean, mobile-ready)*

> "We're using Gemini's on-device model — Gemini Nano — so the app
> pre-sorts spam even without signal. No cloud call. Instant. Private."

---

### 2:45 — The Close (Cherry speaks)

> "BackPocket isn't a tool. It's a staff member that never sleeps,
> never misses an email, and fits in Cherry's back pocket.
> We're ready to scale this to every sole trader in Western Sydney."

> "We're BackPocket. Thank you."

---

## Backup Answers (If Asked)

**"What if Gemini is down?"**
> "We fall back to Ollama running locally on the Mini-PC. Zero dependency on cloud for triage."

**"How does it learn?"**
> "Every time Cherry revises a draft, the correction is stored. Next time a similar email
> arrives from the same sender, the Twin applies what Cherry taught it."

**"Is it secure?"**
> "All API endpoints are protected with an API key. Email is sent via Cherry's own Gmail OAuth.
> Nothing goes through a third-party AI without her permission."

**"Can it handle multiple clients / accountants?"**
> "The architecture supports it — separate sender instruction tables per user.
> That's the enterprise roadmap."

---

## Timing Summary

| Time | Action |
|------|--------|
| 0:00 | Steve the tradie hook |
| 0:30 | Show inbox + triage |
| 1:00 | Approve → email sent → WhatsApp fires |
| 1:45 | Twin chat |
| 2:15 | Mobile API + Flutter + AI Edge |
| 2:45 | Close |
| 3:00 | Done |
