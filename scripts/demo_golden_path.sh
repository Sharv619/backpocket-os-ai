#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# BackPocket OS — Golden Path Demo Readiness Check
# Tests the 3-step Sole Trader lifecycle: Email → Twin → Draft
# Usage: bash scripts/demo_golden_path.sh [BASE_URL]
# ─────────────────────────────────────────────────────────────────────────────

BASE="${1:-http://localhost:8000}"
PASS=0; FAIL=0

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'

ok()   { echo -e "${GREEN}  ✓ PASS${NC} — $1"; ((PASS++)); }
fail() { echo -e "${RED}  ✗ FAIL${NC} — $1"; ((FAIL++)); }
info() { echo -e "${YELLOW}  →${NC} $1"; }

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  BackPocket OS — Golden Path: NSW Pitch Readiness"
echo "  Target: $BASE"
echo "═══════════════════════════════════════════════════════"

# ── 0. ENV VAR PREFLIGHT ──────────────────────────────────────────────────────
echo ""
echo "[ PREFLIGHT — Environment Variables ]"

check_env() {
  if [ -n "${!1}" ]; then
    ok "$1 is set"
  else
    fail "$1 is MISSING — set in .env before demo"
  fi
}

# Load .env if present
[ -f .env ] && export $(grep -v '^#' .env | xargs) 2>/dev/null

check_env GEMINI_API_KEY
check_env OPENROUTER_API_KEY
check_env GOOGLE_APPLICATION_CREDENTIALS

if [ -f "${GOOGLE_APPLICATION_CREDENTIALS:-credentials.json}" ]; then
  ok "credentials.json file EXISTS at ${GOOGLE_APPLICATION_CREDENTIALS:-credentials.json}"
else
  fail "credentials.json NOT FOUND at ${GOOGLE_APPLICATION_CREDENTIALS:-credentials.json}"
fi

if [ -f "token.json" ] || [ -f "token_ywa.json" ]; then
  ok "Gmail OAuth token file found"
else
  fail "No Gmail token file found — run OAuth flow before demo"
fi

# ── 1. HEALTH CHECK ───────────────────────────────────────────────────────────
echo ""
echo "[ STEP 1 — Server Health ]"

HEALTH=$(curl -sf --max-time 5 "$BASE/health" 2>/dev/null)
if [ $? -eq 0 ]; then
  STATUS=$(echo "$HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','UNKNOWN'))" 2>/dev/null)
  DB=$(echo "$HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('checks',{}).get('database','?'))" 2>/dev/null)
  GEMINI=$(echo "$HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('checks',{}).get('gemini_key','?'))" 2>/dev/null)
  OLLAMA=$(echo "$HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('checks',{}).get('ollama','?'))" 2>/dev/null)

  [ "$STATUS" = "READY" ]   && ok "Server status: READY"   || fail "Server status: $STATUS"
  [ "$DB"     = "ok" ]      && ok "Database: connected"    || fail "Database: $DB"
  [ "$GEMINI" = "ok" ]      && ok "Gemini API key: set"    || fail "Gemini key: $GEMINI"
  [ "$OLLAMA" = "ok" ]      && ok "Ollama: reachable"      || info "Ollama: $OLLAMA (optional)"
else
  fail "Server not responding at $BASE — is it running?"
  echo ""
  echo "  Start server: python3 -m uvicorn main:app --host 0.0.0.0 --port 8000"
  exit 1
fi

# ── 2. GOLDEN PATH STEP 1 — Fetch Inbox (Email Ingestion) ────────────────────
echo ""
echo "[ STEP 2 — Golden Path: Fetch Inbox ]"

PENDING=$(curl -sf --max-time 8 "$BASE/api/mobile/pending" 2>/dev/null)
if [ $? -eq 0 ]; then
  COUNT=$(echo "$PENDING" | python3 -c "import sys,json; print(json.load(sys.stdin).get('count',0))" 2>/dev/null)
  ok "/api/mobile/pending responded — $COUNT items in queue"
  if [ "$COUNT" -gt 0 ] 2>/dev/null; then
    SUBJECT=$(echo "$PENDING" | python3 -c "import sys,json; items=json.load(sys.stdin).get('items',[]); print(items[0].get('subject','')[:60] if items else 'none')" 2>/dev/null)
    info "First item: \"$SUBJECT\""
  else
    info "Queue is empty — run: python3 scripts/seed_urgent_email.py to seed demo data"
  fi
else
  fail "/api/mobile/pending failed"
fi

# ── 3. GOLDEN PATH STEP 2 — Digital Twin Chat ────────────────────────────────
echo ""
echo "[ STEP 3 — Golden Path: Digital Twin Processing ]"

CHAT_RESP=$(curl -sf --max-time 30 \
  -X POST "$BASE/api/mobile/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the status of my inbox?"}' 2>/dev/null)

if [ $? -eq 0 ]; then
  TWIN_RESP=$(echo "$CHAT_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('response',''); print(r[:80]+'...' if len(r)>80 else r)" 2>/dev/null)
  [ -n "$TWIN_RESP" ] && ok "Twin responded: \"$TWIN_RESP\"" || fail "Twin returned empty response"
else
  fail "/api/mobile/chat failed or timed out"
fi

# ── 4. GOLDEN PATH STEP 3 — Lead Extraction (AI Pipeline) ───────────────────
echo ""
echo "[ STEP 4 — Golden Path: AI Lead Extraction from Email ]"

LEAD_RESP=$(curl -sf --max-time 20 \
  -X POST "$BASE/api/construction/leads/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "client@example.com",
    "subject": "Need kitchen reno quote ASAP",
    "body": "Hi mate, looking to gut and redo the kitchen. Budget around 18k. Located in Penrith NSW. Need it done before Christmas. Can you come take a look this week?"
  }' 2>/dev/null)

if [ $? -eq 0 ]; then
  LEAD_STATUS=$(echo "$LEAD_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','?'))" 2>/dev/null)
  LEAD_ID=$(echo "$LEAD_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('lead_id','none'))" 2>/dev/null)
  [ "$LEAD_STATUS" = "success" ] && ok "Lead extracted — ID: $LEAD_ID" || fail "Lead extraction failed: $LEAD_STATUS"
else
  fail "/api/construction/leads/extract failed or timed out"
fi

# ── 5. SOVEREIGNTY CHECK ─────────────────────────────────────────────────────
echo ""
echo "[ STEP 5 — Data Sovereignty Confirmation ]"

STATUS_RESP=$(curl -sf --max-time 5 "$BASE/api/status" 2>/dev/null)
if [ $? -eq 0 ]; then
  PRIV=$(echo "$STATUS_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('privacy_mode','false'))" 2>/dev/null)
  RESID=$(echo "$STATUS_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data_residency','unknown'))" 2>/dev/null)
  [ "$PRIV" = "True" ] && ok "Privacy Mode: ACTIVE" || fail "Privacy Mode: OFF"
  [ "$RESID" = "local" ] && ok "Data Residency: LOCAL" || fail "Data Residency: $RESID"
else
  fail "/api/status failed"
fi

# ── RESULT ───────────────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════"
TOTAL=$((PASS + FAIL))
if [ $FAIL -eq 0 ]; then
  echo -e "${GREEN}  ✓ ALL $TOTAL CHECKS PASSED — PITCH READY${NC}"
else
  echo -e "${RED}  ✗ $FAIL/$TOTAL CHECKS FAILED — NOT READY${NC}"
  echo ""
  echo "  Fix failures above before Tuesday's demo."
fi
echo "═══════════════════════════════════════════════════════"
echo ""
exit $FAIL
