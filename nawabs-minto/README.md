# Nawab's Minto — Order Manager

Internal order management + driver dispatch for Nawab's Minto. Orders are phoned/WhatsApp'd
in by customers and logged by staff — there is no customer-facing ordering flow in this app.

Two interfaces, one codebase:

- **`/dashboard`** — shop counter web app. Staff log orders, run the Kanban queue, assign
  drivers, and pull reports.
- **`/driver`** — mobile-first PWA. Drivers see their assignment, navigate, and update status.
  Installable to a phone home screen (Add to Home Screen / "Install app").

## Tech stack

React + Vite + TypeScript + Tailwind CSS, on Firebase (Firestore, Auth, Cloud Functions, FCM,
Hosting). Real-time sync via Firestore listeners — no polling anywhere.

## Project layout

```
src/
  types/            Shared domain types (Order, Driver, Staff, status enums)
  lib/               Firebase init, formatting, status/urgency logic, CSV export, notification sound
  hooks/             useStaffAuth, useDriverAuth, useOrders, useDrivers, dashboard alerts, FCM registration
  components/
    dashboard/       New order form, order card, assign/cancel modals, toasts
    driver/          Order card, issue-flag modal
    shared/          ProtectedRoute
  pages/
    dashboard/       Login, Board (Kanban), Drivers, History
    driver/          Login, Home, History
functions/           Cloud Functions: driver PIN login, driver PIN reset, FCM + currentOrderId sync
firestore.rules       Security rules (staff vs. driver access)
firestore.indexes.json
firebase.json
```

## Setup

### 1. Create the Firebase project

In the [Firebase console](https://console.firebase.google.com): create a project, then enable
**Firestore**, **Authentication** (Email/Password provider), **Cloud Messaging**, and
**Hosting**. Note the web app config from *Project settings → General → Your apps*.

### 2. Configure the frontend

```bash
cp .env.example .env
# fill in the VITE_FIREBASE_* values from the Firebase console
npm install
npm run dev
```

Also update `public/firebase-messaging-sw.js` with the same config — service workers can't
read Vite env vars, so it's a separate hardcoded copy used only for background push.

Get `VITE_FIREBASE_VAPID_KEY` from *Cloud Messaging → Web configuration → Web Push
certificates → Generate key pair*.

### 3. Deploy Firestore rules, indexes, and Cloud Functions

```bash
npm install -g firebase-tools   # if you don't have it
firebase login
# update .firebaserc with your real project id
firebase deploy --only firestore:rules,firestore:indexes,functions
```

### 4. Create your first staff login

In Firebase Auth, add a user (email/password). Then in Firestore, create a document at
`staff/{that user's uid}`:

```json
{ "name": "Owner", "email": "owner@example.com", "role": "owner" }
```

The doc id **must** equal the Auth user's uid — that's how Firestore rules recognize staff.
Sign in at `/dashboard/login`.

### 5. Add a driver

Create a `drivers/{driverId}` document (any id):

```json
{ "name": "Sam", "phone": "0412345678", "status": "offline", "currentOrderId": null, "fcmToken": null }
```

Then, signed in as staff, call the `setDriverPin` Cloud Function once to set their PIN (e.g.
from the browser devtools console on `/dashboard`, with the Firebase SDK already loaded, or
via `firebase functions:shell`):

```js
import { getFunctions, httpsCallable } from "firebase/functions";
await httpsCallable(getFunctions(), "setDriverPin")({ driverId: "<id>", pin: "1234" });
```

The driver can now sign in at `/driver/login` with their phone number + that PIN.

### 6. Deploy

```bash
npm run build
firebase deploy --only hosting
```

## Local development against the emulator suite

```bash
firebase emulators:start
# in another terminal, with VITE_USE_EMULATORS=1 in .env
npm run dev
```

## Notes on the data model

- Orders carry a full timestamp trail (`createdAt` → `acceptedAt` → `readyAt` → `pickedUpAt`
  → `deliveredAt`) so History can compute average delivery time without re-deriving it.
- There's no customer-facing order API yet, but `orders` is a flat Firestore collection with
  a `createdBy` field — a future intake webhook/Cloud Function can write directly into it
  without touching the dashboard or driver app.
- A driver may only update their own assigned order's `status`/`pickedUpAt`/`deliveredAt`/`issue`
  fields (enforced in `firestore.rules`) — they can't reassign orders or edit pricing.
- `drivers.currentOrderId` is kept in sync by a Cloud Function trigger; the dashboard's driver
  panel additionally cross-checks the live `orders` feed so it never shows stale state.

## Known v1 limitations (by design, per the brief)

- No customer-facing ordering, no online payment processing.
- One shared `auth` session per browser — don't open `/dashboard` and `/driver` signed in as
  different people in the same browser profile.
- PWA icons are placeholder art (`public/icons/icon.svg` rendered to PNG) — swap before a real
  app store / production install push.
