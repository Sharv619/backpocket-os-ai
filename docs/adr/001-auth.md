# ADR 001: Authentication Provider Selection

**Date:** 2026-04-13
**Status:** Proposed
**Decision:** Supabase Auth

---

## Context

BackPocket OS needs a robust, scalable, and cost-effective authentication solution that supports multi-tenancy, Google SSO, and seamless integration with both a Flutter frontend and a FastAPI backend. Row-Level Security (RLS) integration with Postgres is a critical factor.

### Decision Drivers
*   **Cost-effectiveness:** Prioritize solutions with a generous free tier or low operational cost.
*   **Ease of integration:** Simple to integrate with Flutter (frontend) and FastAPI (backend).
*   **Google SSO:** Must support Google sign-in out-of-the-box.
*   **Multi-tenancy support:** Ability to isolate user data per "tradie business."
*   **RLS compatibility:** Strong integration capabilities with PostgreSQL Row-Level Security.
*   **Developer experience:** Good documentation and community support.
*   **Scalability:** Ability to scale with user growth.
*   **Self-hosting/Data Sovereignty (Secondary):** While not a primary driver for the IdP itself (as most are SaaS), solutions that offer more control or transparency are a plus.

---

## Evaluation

### Supabase Auth
*   **Pros:**
    *   **Open Source:** The core is open source, offering transparency and potential for self-hosting (though typically used as a managed service).
    *   **Generous Free Tier:** Very comprehensive free tier for authentication and database, offering 50k MAU.
    *   **Deep Postgres Integration:** Built specifically for PostgreSQL, making RLS integration exceptionally seamless. It often manages RLS policies directly or provides clear patterns, with JWT containing `sub` claim mapping directly to `user_id`.
    *   **Flutter & FastAPI SDKs:** Excellent Flutter SDK (`supabase_flutter`) and straightforward JWT-based integration with FastAPI.
    *   **Google SSO:** Fully supported.
    *   **Database-first:** Auth is tightly coupled with the PostgreSQL database, which aligns with our RLS requirements.
    *   **Managed Service:** Offers managed hosting, reducing operational overhead.
    *   **Magic Link:** Email-first for tradies who might not have Gmail on job site.
*   **Cons:**
    *   **Learning Curve:** While powerful, the "database-first" approach and some concepts can have a slight learning curve.
    *   **Vendor Lock-in (soft):** Tightly coupled with Supabase's ecosystem.
    *   **Not a pure IdP:** While it provides auth, it's part of a larger backend-as-a-service platform.

### Clerk
*   **Pros:**
    *   **Dedicated IdP:** Designed purely for authentication and user management, often leading to a highly focused and optimized product.
    *   **Excellent Developer Experience:** Known for highly intuitive SDKs and comprehensive documentation, especially for frontend frameworks.
    *   **Flutter & FastAPI Integration:** Offers a Flutter SDK and clear guides for integrating with custom backends like FastAPI (via JWT verification).
    *   **Google SSO:** Fully supported with easy setup.
    *   **Multi-tenancy:** Strong support for organizations/multi-tenancy models.
    *   **Managed Service:** Fully managed SaaS, minimal operational burden.
    *   **Flexible UI Components:** Provides pre-built, customizable UI components for Flutter.
*   **Cons:**
    *   **Cost:** While it has a free tier (25k MAU), it can become more expensive than Supabase as user count grows, especially for advanced features.
    *   **RLS Integration:** Requires manual JWT verification in FastAPI and then using the decoded `user_id` to enforce RLS in Postgres. This is entirely feasible but less "out-of-the-box" than Supabase's integrated approach.
    *   **Not Open Source:** Proprietary solution.

### Auth.js
*   **Pros:** Open source, flexible.
*   **Cons:** Self-hosted needed (adds infra complexity), no managed Google SSO, PostgreSQL integration requires custom JWT handling.

### Cloudflare Access
*   **Pros:** Integrates well with Cloudflare ecosystem.
*   **Cons:** Not a primary IdP for user authentication, more for access control to applications.
---

## Decision: **Supabase Auth**

**Reasoning:**

Supabase Auth is the superior choice for BackPocket OS primarily due to its **deep, native integration with PostgreSQL and Row-Level Security (RLS)**, combined with its **generous free tier**. Given our emphasis on "local-first" and data sovereignty (even if the IdP is SaaS), a system designed around PostgreSQL and offering transparent, open-source components (even if managed) aligns better with our long-term vision.

The seamless RLS integration offered by Supabase significantly reduces development complexity and potential for errors when enforcing multi-tenant data isolation. While Clerk offers an excellent developer experience and is a strong contender for pure authentication, its cost structure and more manual approach to RLS integration make it a slightly less optimal fit for our specific constraints and priorities.

We can leverage Supabase's managed Postgres instance for initial rapid deployment and potentially explore self-hosting its components or migrating to an Oracle-hosted Postgres later if extreme data sovereignty becomes a hard requirement for the auth layer itself.

## Consequences
*   We will adopt Supabase's Flutter SDK for frontend authentication and its JWT validation for FastAPI.
*   We will explicitly define and manage RLS policies within our PostgreSQL database, leveraging Supabase's patterns.
*   We will monitor Supabase's pricing model as we scale, though the free tier should cover initial customer acquisition.
*   The tight coupling with Supabase's ecosystem should be noted but is deemed acceptable given its benefits for our data layer.

---

## Implementation Plan

```python
# main.py - Supabase JWT validation
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

def get_current_user(authorization: str) -> dict:
    """Extract user from Authorization: Bearer <token>"""
    token = authorization.replace("Bearer ", "")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    user = supabase.auth.get_user(token)
    return {"id": user.id, "email": user.email}

# Use in routes:
@app.get("/api/construction/leads")
def get_leads(user = Depends(get_current_user)):
    # RLS enforced via Postgres policies
    return db.query("SELECT * FROM leads WHERE user_id = %s", user["id"])
```

```dart
// Flutter api_client.dart
import 'package:supabase_flutter/supabase_flutter.dart';

await Supabase.initialize(
  url: 'https://xxx.supabase.co',
  anonKey: 'xxx',
);

final res = await supabase.auth.signInWithOAuth(Google());
// Magic link alternative:
await supabase.auth.signInWithOtp(email: 'tradie@gmail.com');
```

---

## RLS Integration

```sql
-- Postgres: Enable RLS
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE quotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own data
CREATE POLICY "Users can view own leads" ON leads
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own leads" ON leads
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own leads" ON leads
    FOR UPDATE USING (auth.uid() = user_id);
```

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|-------|-------------|
| Supabase downtime | Low | High | Cache tokens in localStorage, retry on 401 |
| Free tier limit exceeded | Medium | High | Implement usage metering, warn at 40k |
| User migration pain | Medium | Medium | Export/import via Supabase CLI |

---

## Timeline

- **Day 5**: Supabase project setup
- **Day 6**: Google OAuth credentials
- **Day 7**: `POST /api/auth/login` endpoint
- **Day 8**: Flutter login screen
- **Day 9**: RLS policies migration

---

## References

- [Supabase Auth Docs](https://supabase.com/docs/guides/auth)
- [Supabase Flutter SDK](https://pub.dev/packages/supabase_flutter)
- [Postgres RLS](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)