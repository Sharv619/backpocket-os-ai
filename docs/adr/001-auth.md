# ADR 001: Authentication Provider Selection

**Date:** 2026-04-13
**Status:** Proposed
**Decision:** Supabase Auth

---

## Context

BackPocket OS needs multi-tenant authentication for:
1. Flutter mobile app users (tradies)
2. Web dashboard users (sole traders)
3. Future team features (marketers, admins)

Constraints:
- **$0 cost** preferred (seed stage)
- **Google SSO** required (tradies use Gmail)
- **Postgres RLS** integration needed
- No on-prem/self-hosted IdP (we're cloud-only on Oracle)

---

## Options Considered

| Provider | Cost | Google SSO | RLS | Integration Effort |
|----------|------|-----------|-----|-------------------|
| **Supabase Auth** | Free tier (50k MAU) | ✅ | ✅ Built-in | Low |
| **Clerk** | Free tier (25k MAU) | ✅ | ❌ Manual sync | Medium |
| **Auth.js** | Free | ✅ | ❌ Manual | High |
| **Cloudflare Access** | Free tier | ✅ | ❌ Not applicable | Medium |

---

## Decision: **Supabase Auth**

### Why Supabase

1. **Zero cost** — 50k monthly active users on free tier is plenty for our target.
2. **Built-in RLS** — User-scoped data access without extra code.
3. **Postgres native** — JWT contains `sub` claim, maps directly to `user_id`.
4. **Flutter SDK** — `supabase_flutter` package is battle-tested.
5. **Magic Link** — Email-first for tradies who might not have Gmail on job site.

### Why NOT Clerk

- Lower free tier (25k MAU vs 50k)
- No built-in RLS integration — requires manual sync to Postgres
- More expensive after free tier ($0.50/user/month vs Supabase's overage)

### Why NOT Auth.js

- Self-hosted needed — adds infra complexity
- No managed Google SSO — needs OAuth creds setup manually
- PostgreSQL integration requires custom JWT handling

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