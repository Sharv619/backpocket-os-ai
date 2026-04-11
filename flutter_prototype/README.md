# BackPocket Mobile — Flutter + Gemini Architecture

## The Vision

Cherry is a sole-trader accountant. She can't sit at a computer all day.
With the BackPocket mobile app, she approves emails from her phone in one tap,
gets real-time WhatsApp alerts, and her AI twin handles the rest.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Cherry's iPhone / Android               │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Flutter App (Dart)                       │   │
│  │                                                  │   │
│  │  ┌──────────────┐    ┌──────────────────────┐   │   │
│  │  │  Inbox View  │    │  Twin Chat View       │   │   │
│  │  │              │    │                       │   │   │
│  │  │  [URGENT] ●  │    │  "What needs         │   │   │
│  │  │  Steve - inv │    │   attention today?"  │   │   │
│  │  │  [HIGH]      │    │                       │   │   │
│  │  │  Angela - BAS│    │  ← Gemini response   │   │   │
│  │  │              │    │                       │   │   │
│  │  │  [Approve ✓] │    │  [Send]               │   │   │
│  │  └──────────────┘    └──────────────────────┘   │   │
│  │                                                  │   │
│  │  ┌──────────────────────────────────────────┐   │   │
│  │  │  Gemini Nano (on-device, offline)        │   │   │
│  │  │  → Pre-sorts SPAM before server call     │   │   │
│  │  │  → Works without internet                │   │   │
│  │  └──────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────┘   │
└───────────────────────┬─────────────────────────────────┘
                        │  HTTPS (X-API-Key header)
                        ▼
┌─────────────────────────────────────────────────────────┐
│              BackPocket OS Server                        │
│           (FastAPI + SQLite + Gemini 2.5 Flash)         │
│                                                         │
│  GET  /api/mobile/pending  → inbox for mobile           │
│  POST /api/mobile/approve  → one-tap approve            │
│  POST /api/mobile/chat     → talk to twin               │
│                                                         │
│              ↓               ↓               ↓          │
│          Gmail API       WhatsApp         Google        │
│          (send email)    (notify)         Sheets        │
└─────────────────────────────────────────────────────────┘
```

---

## API Endpoints (Already Live)

### `GET /api/mobile/pending`
Returns the inbox sorted by priority tier.

```json
{
  "count": 2,
  "items": [
    {
      "ref_id": "DEMO-00001",
      "sender": "steve.thompson@builditright.com.au",
      "subject": "URGENT: Invoice #4821 overdue - cash flow critical",
      "tier": 1,
      "tier_label": "URGENT",
      "preview": "Hi Steve, I've reviewed invoice #4821...",
      "age_hours": 2.5
    }
  ]
}
```

### `POST /api/mobile/approve`
One-tap approve from mobile.

```json
// Request
{ "ref_id": "DEMO-00001", "note": "approved via mobile" }

// Response
{
  "status": "approved",
  "ref_id": "DEMO-00001",
  "message": "Draft sent to steve.thompson@builditright.com.au"
}
```

### `POST /api/mobile/chat`
Talk to the Twin AI.

```json
// Request
{ "message": "What emails need attention today?" }

// Response
{
  "response": "You have 2 urgent items: Steve's invoice #4821 is overdue...",
  "conversation_id": "conv_abc123"
}
```

---

## Flutter Package Stack

```yaml
# pubspec.yaml
dependencies:
  flutter: sdk: flutter
  http: ^1.2.0                    # API calls to BackPocket server
  google_generative_ai: ^0.4.0    # Gemini API (cloud + on-device)
  shared_preferences: ^2.2.0      # Store API key locally
  flutter_local_notifications: ^17.0.0  # Local alerts
```

---

## The "AI Edge" Story

**Why this matters for Cherry:**

| Scenario | Without AI Edge | With AI Edge (Gemini Nano) |
|----------|----------------|---------------------------|
| On the job site (no signal) | App unusable | Pre-sorts spam locally, queues for later |
| Poor connection | Slow AI responses | Device handles Tier 4-5, server handles 1-3 |
| Privacy-sensitive clients | All data goes to cloud | Tier 4-5 never leaves device |
| Cost | API call for every email | Free for spam detection |

**Flow:**
1. Email arrives → BackPocket server triages with Gemini 2.5 Flash
2. Flutter app opens → Gemini Nano on device **re-validates** tier locally
3. Tier 4-5 (Low/Spam): handled or dismissed on device, never needs server call
4. Tier 1-3 (Urgent/High/Medium): full server context, WhatsApp notification fires

---

## Demo Flow (3 minutes)

1. Open Flutter app → inbox shows 5 emails, URGENT at top
2. Tap DEMO-00001 (Steve's invoice) → see AI-drafted reply
3. Tap "Approve" → server sends email + WhatsApp fires on Cherry's phone
4. Open chat → type "what's overdue?" → Twin responds with context
5. Show offline mode → Gemini Nano flags SPAM-00005 without server call

---

## Why Flutter Over React Native?

- Single codebase for iOS + Android + Web
- `google_generative_ai` Flutter package has first-class Gemini support
- Hot reload = fast iteration at the hackathon
- Cherry's team likely uses mixed devices (Android tradies, iOS accountants)

---

*BackPocket OS — Your business in your back pocket.*
