# AI Governance Handbook — TL;DR (Pocket Card)

**Full version:** `docs/AI_GOVERNANCE_HANDBOOK.md`

---

## PR Checklist (Copy to Every AI PR)

- [ ] HITL preserved — no bypass of `pending_approvals`
- [ ] Prompt reviewed for bias + injection risk
- [ ] Data flow documented — what PII goes where?
- [ ] Local-first respected — cloud is fallback only
- [ ] Non-reliance disclaimer present
- [ ] Audit trail — logged to `audit_log`
- [ ] RAG corrections still apply
- [ ] AI JSON output schema-validated
- [ ] Rollback plan exists
- [ ] Passes all 4 mental models below

---

## 4 Mental Models

| Test | Ask Yourself |
|------|-------------|
| **Regulator** | Would OAIC/ATO be comfortable with this? |
| **Steve** | Would our tradie user understand and trust this? |
| **Front-Page** | Would this embarrass us in the news? |
| **Trust** | Does this build trust or feel like AI going behind user's back? |

---

## Never Do

1. Auto-send customer-facing content (HITL mandatory)
2. Send PII to cloud AI without redaction
3. Store API keys in code
4. Let AI set final prices
5. Bypass voice confirmation gate

---

## Top 3 Gaps (Fix Now)

1. **PII redaction missing** before OpenRouter calls → `_redact_pii()` needed
2. **No `/privacy` page** → APP 1 requires published privacy policy
3. **No consent flow** on first run → APP 5 notification

---

*Last updated: 2026-04-19 | Review: every 90 days*
