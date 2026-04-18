import os
import sys
import io
import logging
import json
import requests
import math
import re
from google import genai  # google-genai (new SDK) — exposes genai.Client
from dotenv import load_dotenv
from datetime import datetime

if sys.platform == "win32":
    try:
        if sys.stdout.buffer is not None:
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding="utf-8", errors="replace"
            )
        if sys.stderr.buffer is not None:
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer, encoding="utf-8", errors="replace"
            )
    except Exception:
        pass

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---- In-memory whitelist cache (refreshed every 5 minutes) ----
_client_whitelist_cache = set()
_domain_whitelist_cache = set()
_priority_list_cache = {}
_cache_last_loaded = None
_CACHE_TTL_SECONDS = 300


def _get_client_whitelist() -> tuple:
    """Returns a tuple of (set(emails), set(domains)) from Clients_Master sheet.
    Results are cached for 5 minutes."""
    global _client_whitelist_cache, _domain_whitelist_cache, _cache_last_loaded
    now = datetime.now()
    if (
        _cache_last_loaded
        and (now - _cache_last_loaded).total_seconds() < _CACHE_TTL_SECONDS
    ):
        return _client_whitelist_cache, _domain_whitelist_cache

    try:
        from services.google_sheets import get_client_emails

        emails = get_client_emails()
        _client_whitelist_cache = {e.lower().strip() for e in emails if e}

        # Extract domains for the 'Company Shield'
        domains = set()
        for e in _client_whitelist_cache:
            if "@" in e:
                domains.add(e.split("@")[1])
        _domain_whitelist_cache = domains

        _cache_last_loaded = now
        logger.info(
            f"WHITELIST: Loaded {len(_client_whitelist_cache)} emails & {len(_domain_whitelist_cache)} domains."
        )

        # Also load priority list
        try:
            from services.google_sheets import get_priority_list

            _priority_list_cache.update(get_priority_list())
        except Exception as e:
            logger.error(f"❌ PRIORITY LIST LOAD FAIL: {e}")

    except Exception as e:
        logger.error(f"❌ WHITELIST LOAD FAIL: {e}. Using stale cache.")

    return _client_whitelist_cache, _domain_whitelist_cache


def _get_cached_priority_list():
    """Returns priority list from cache since it's loaded with whitelist."""
    global _priority_list_cache
    if (
        not _cache_last_loaded
        or (datetime.now() - _cache_last_loaded).total_seconds() >= _CACHE_TTL_SECONDS
    ):
        # Force a refresh if needed
        _get_client_whitelist()
    return _priority_list_cache


# ────────────────────────────────────────────────────────────────────
# COST OPTIMIZATION: ML-based API Router (from Network Guardian)
# ────────────────────────────────────────────────────────────────────


def _sanitize_text(text: str) -> str:
    """Sanitize text for entropy calculation."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]", "", text)
    return text[:100]  # First 100 chars only


def calculate_entropy(text: str) -> float:
    """Calculate Shannon entropy to determine email complexity.
    Uses ML algorithm from Network Guardian AI for cost optimization."""
    sanitized = _sanitize_text(text)
    if not sanitized:
        return 0.0

    probs = [float(sanitized.count(c)) / len(sanitized) for c in set(sanitized)]
    entropy = -sum(p * math.log2(p) for p in probs if p > 0)
    digit_ratio = sum(c.isdigit() for c in sanitized) / len(sanitized)

    return round(entropy + (digit_ratio * 2), 2)


def _should_use_full_ai(email_content: dict, tier: int) -> bool:
    """Determine if email needs full AI processing (cost optimization).

    - Low entropy (< 3.0): Use template
    - Medium entropy (3.0-4.0): Use Ollama
    - High entropy (> 4.0): Use OpenRouter/Gemini
    """
    subject = email_content.get("subject", "")
    snippet = email_content.get("snippet", "")

    entropy_score = calculate_entropy(subject + " " + snippet)

    # Tier 1 always gets full AI (important clients)
    if tier in ["1", 1]:
        return True

    # High entropy emails get full AI
    return entropy_score > 3.5


def get_gemini_client():
    """Initializes and returns the Gemini AI client."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return None

    client = genai.Client(api_key=api_key)
    return client


def test_gemini_connection():
    """Tests the connection to Gemini API with a simple prompt."""
    try:
        client = get_gemini_client()
        if not client:
            return {"status": "error", "message": "Gemini API key missing or invalid"}

        response = client.models.generate_content(
            model="gemini-2.5-flash", contents="Say 'Gemini connected successfully'"
        )
        response_text = (
            response.text.strip() if response and response.text else "Connected"
        )
        return {"status": "success", "message": response_text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_ollama_response(prompt, json_mode=False):
    """Primary local LLM call via Ollama (Zero Cost, No Limits, Better Privacy)."""
    import re

    try:
        model = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
        url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/api/generate")

        payload = {"model": model, "prompt": prompt, "stream": False}
        if json_mode:
            payload["format"] = "json"

        response = requests.post(url, json=payload, timeout=180)
        if response.status_code == 200:
            raw_text = response.json().get("response", "")
            # Strip any thinking tags if present
            clean_text = re.sub(
                r"<think>.*?</think>", "", raw_text, flags=re.DOTALL
            ).strip()
            logger.info(f"Ollama response received ({len(clean_text)} chars)")
            return clean_text
        else:
            logger.error(f"Ollama error: {response.status_code}")
            return None
    except Exception as e:
        logger.warning(f"Ollama not available: {e}")
        return None


def get_local_ai_response(
    prompt, sys_prompt="You are a helpful assistant.", json_mode=False
):
    """Call local AI server on the same WiFi network (private, no cloud)."""
    local_url = os.getenv("LOCAL_AI_URL", "").rstrip("/")
    if not local_url:
        return None

    payload = {
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt},
        ]
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    try:
        response = requests.post(
            f"{local_url}/api/chat",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )
        if response.status_code == 200:
            data = response.json()
            # Support both OpenAI-style and plain {response: ...} formats
            if "choices" in data:
                return data["choices"][0]["message"]["content"]
            return data.get("response") or data.get("content") or data.get("text")
        else:
            logger.error(f"Local AI Error: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Local AI request failed: {e}")
        return None


def get_openrouter_response(
    prompt,
    model="openai/gpt-4o",
    sys_prompt="You are a helpful assistant.",
    json_mode=False,
):
    """Call AI: local server first (private), OpenRouter as fallback."""
    # 1. Try local AI first (private, on-prem)
    local_result = get_local_ai_response(
        prompt, sys_prompt=sys_prompt, json_mode=json_mode
    )
    if local_result:
        logger.info("Using local AI server (private mode).")
        return local_result

    # 2. Fallback to OpenRouter (cloud)
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.warning(
            "LOCAL_AI_URL not set and OPENROUTER_API_KEY missing — Coach unavailable."
        )
        return None

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://backpocket.os",
        "X-Title": "BackPocket OS",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt},
        ],
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            logger.error(f"OpenRouter Error: {response.text}")
            return None
    except Exception as e:
        logger.error(f"OpenRouter Request failed: {e}")
        return None


def analyze_draft_with_coach(email_content, draft_response):
    """
    Phase 5 / Coach Integration:
    Passes the draft to GPT-4o via OpenRouter to act as a Communication Coach.
    Returns confidence score, feedback, and a Power Version.
    """
    sys_prompt = "You are Steve's Communication Coach (GPT-4o). Your job is to analyze her email drafts."
    prompt = f"""
Please analyze this drafted email reply to a client.

CLIENT EMAIL:
Subject: {email_content.get("subject")}
Body: {email_content.get("snippet")}

DRAFTED REPLY:
{draft_response}

Your task:
Provide a JSON object containing:
1. "confidence_score": An integer from 1-100 indicating how strong and confident the tone is (50-69 = "Needs work", 70-89 = "Good", 90+ = "Excellent").
2. "feedback": 1-2 bullet points of constructive tone/style analysis.
3. "power_version": A suggested rewritten "Power Version" that is direct, warm, and professional.

Return ONLY the raw JSON string. Do not wrap in markdown or backticks.
"""
    import json

    res = get_openrouter_response(
        prompt, model="openai/gpt-4o", sys_prompt=sys_prompt, json_mode=True
    )
    if res:
        try:
            return json.loads(res)
        except Exception as e:
            logger.error(f"Failed to parse Coach JSON: {e}")
    return None


def pre_triage_rules(email_content):
    """
    LAYER 0: Zero-Cost Rule-Based (pre_triage_rules).

    WHITELIST OVERRIDE runs FIRST: If the sender is a known client, we
    immediately return Tier 1 and skip all other rules. This prevents any
    existing client from ever being mis-classified as spam or archived.

    Standard checks run only for unknown senders.
    """
    sender_email = (
        str(email_content.get("clean_email") or email_content.get("sender") or "")
        .lower()
        .strip()
    )
    subject = email_content.get("subject", "").lower()
    snippet = email_content.get("snippet", "").lower()
    has_attachments = email_content.get("has_attachments", False)
    sender_domain = sender_email.split("@")[1] if "@" in sender_email else ""

    # =====================================================================
    # WHITELIST & ONBOARDING (Layer 0 – Priority 0)
    # =====================================================================
    priority_list = _get_cached_priority_list()

    # Check if sender email or domain is in the dynamic priority list
    if sender_email in priority_list:
        logger.info(
            f"🌟 DYNAMIC PRIORITY HIT (Email): {sender_email} — forcing Tier {priority_list[sender_email]}."
        )
        return {
            "tier": priority_list[sender_email],
            "reason": "Dynamic priority sender (Sheet)",
        }

    if sender_domain in priority_list:
        logger.info(
            f"🌟 DYNAMIC PRIORITY HIT (Domain): {sender_domain} — forcing Tier {priority_list[sender_domain]}."
        )
        return {
            "tier": priority_list[sender_domain],
            "reason": "Dynamic priority domain (Sheet)",
        }

    # 🆕 SPECIAL CASE: "New User Registered" Auto-Flow
    if "new user registered" in subject or "new client registered" in subject:
        logger.info(f"🆕 ONBOARDING TRIGGER: {subject}")
        return {
            "tier": 1,
            "reason": "New User Registered alert detected.",
            "is_onboarding_triggered": True,
            "actionable_items": "Review new portal registration.",
            "needs_hitl_check": False,
        }

    # 🏢 Suitedash Portal Updates (MUST CHECK BEFORE whitelist - emails come FROM cherry@yourwebaccountant.com)
    if "cherry@yourwebaccountant.com" in sender_email:
        portal_keywords = [
            "project",
            "portal",
            "missed",
            "due",
            "appointment",
            "daily digest",
            "planning",
        ]
        if any(k in subject.lower() for k in portal_keywords):
            has_activity = (
                "no activity" not in snippet.lower()
                and "completed" not in snippet.lower()
            )
            logger.info(f"PORTAL UPDATE (appointment/project): Activity={has_activity}")
            return {
                "tier": 4,
                "reason": f"Suitedash Portal Update ({'Action Needed' if has_activity else 'No Activity'}).",
                "is_portal_update": True,
                "is_portal_digest": True,
                "has_activity": has_activity,
                "actionable_items": "Check portal for updates."
                if has_activity
                else "None",
                "needs_hitl_check": has_activity,
            }
        else:
            logger.info("SUITEDASH EMAIL (other): Defaulting to Tier 4.")
            return {
                "tier": 4,
                "reason": "Suitedash Portal Email - Log and check.",
                "is_portal_update": True,
                "has_activity": True,
                "actionable_items": "Check portal if needed.",
                "needs_hitl_check": False,
            }

    # 💎 Steve's "Golden Senders" (Tier 1 - STAY IN INBOX)
    tier_1_overrides = [
        "jco064690@gmail.com",
        "trustdeed.com.au",
        "gjcctax.au",
        "cqstax.com",
        "almemmolos@gmail.com",
        "johnwatts.com.au",
        "david@vdmandthorn.com",
        "che.tomenio1@gmail.com",  # Known potential client asking about tax returns
    ]
    whitelist_emails, whitelist_domains = _get_client_whitelist()

    tier_override = None
    if any(x in sender_email for x in tier_1_overrides) or any(
        x in sender_domain for x in tier_1_overrides
    ):
        logger.info(
            f"🌟 TIER 1 OVERRIDE: {sender_email} — forcing Tier 1 (No Archive)."
        )
        tier_override = 1
    elif sender_email in whitelist_emails:
        logger.info(f"🛡️ WHITELIST HIT (Email): {sender_email} — forcing Tier 1.")
        tier_override = 1
    elif sender_domain in whitelist_domains and sender_domain not in [
        "gmail.com",
        "outlook.com",
        "hotmail.com",
        "yahoo.com",
        "icloud.com",
    ]:
        logger.info(f"🛡️ WHITELAIL HIT (Domain): {sender_domain} — forcing Tier 1.")
        tier_override = 1

    # 🏛️ Tier 2: Govt / Assoc / Specific Shields (STAY IN INBOX)
    tier_2_overrides = [
        "ato.gov.au",
        "asic.gov.au",
        "auditorsinstitute.com",
        "auditorsintitute.com",
        "publicaccountants.org.au",
        "ifpa.com.au",
        "ndiscommission.gov.au",
        "stripe.com",
        "cloudoffis",
    ]
    if any(x in sender_email for x in tier_2_overrides) or any(
        x in sender_domain for x in tier_2_overrides
    ):
        logger.info(f"🏛️ TIER 2 OVERRIDE: {sender_email} — forcing Tier 2 (No Archive).")
        tier_override = 2

    # ▫️ Tier 3: Routine Suppliers (Log to Supplier_Expenses, STAY IN INBOX)
    tier_3_overrides = [
        "superloop.com",
        "bigbosscleaning.com.au",
        "whapi.cloud",
        "telstra.com",
        "nab.com.au",
        "anz.com",
        "appsumo.com",
        "pinch.com.au",
        "suitedash.com",
        "linkedin.com",
        "simplefund360",
    ]
    if any(x in sender_email for x in tier_3_overrides) or any(
        x in sender_domain for x in tier_3_overrides
    ):
        logger.info(
            f"TIER 3 SUPPLIER: {sender_email} — Log to Supplier_Expenses, stay in Inbox."
        )
        tier_override = 3

    # 📱 Business 1300 / Suitedash Digests handled below...

    # 📱 Business 1300 Call Centre Messages
    if (
        "messages@business1300.com.au" in sender_email
        and "call centre message" in subject
    ):
        logger.info("☎️ CALL CENTRE MESSAGE: Forcing Tier 2 (Action Queue) - URGENT!")
        return {
            "tier": 2,
            "reason": "URGENT - Business 1300 Call Centre Message.",
            "is_call_centre": True,
            "is_urgent": True,
            "actionable_items": "⚠️ URGENT - Review call message and reply/call back immediately!",
            "needs_hitl_check": False,
        }

    # 🆕 Suitedash New Client Registrations (cherry@yourwebaccountant.com) - ONLY for registration emails
    if "cherry@yourwebaccountant.com" in sender_email and (
        "registration" in subject.lower()
        or "new user" in subject.lower()
        or "welcome" in subject.lower()
    ):
        logger.info("SUITEDASH NEW CLIENT: Forcing Tier 1 with auto-onboard.")
        return {
            "tier": 1,
            "reason": "Suitedash New Client Registration - Auto-extract and onboard.",
            "is_new_client_registration": True,
            "actionable_items": "Extract client details and add to Clients_Master.",
            "needs_hitl_check": False,
        }

    # 🏢 Suitedash Portal Digests (Big Boss Accountants :: Planning - Daily Digest)
    if (
        "planning - daily digest" in subject.lower()
        or "planning daily digest" in subject.lower()
    ):
        has_activity = (
            "no activity" not in snippet.lower()
            and "no new activity" not in snippet.lower()
        )
        logger.info(f"PORTAL DIGEST: Activity={has_activity}")
        return {
            "tier": 4,
            "reason": f"Suitedash Daily Digest ({'Active' if has_activity else 'No Activity'}).",
            "is_portal_update": True,
            "is_portal_digest": True,
            "has_activity": has_activity,
            "actionable_items": "Reminder: Check Suitedash activity."
            if has_activity
            else "None",
            "needs_hitl_check": has_activity,
        }

    if "document has been signed" in subject:
        logger.info(
            "✍️ DOC SIGNED: Forcing Tier 2 (Log to Portal_Updates, Keep in Inbox)."
        )
        return {
            "tier": 2,
            "reason": "Document has been signed - Needs filing.",
            "is_portal_update": True,
            "is_doc_signed": True,
            "actionable_items": "File attachment to Client Folder (Phase 2).",
            "needs_hitl_check": True,
        }

    if tier_override:
        return {
            "tier": tier_override,
            "reason": f"Whitelist Override: Known {'Email' if sender_email in whitelist_emails else 'Company Domain'} — Action Queue Guaranteed.",
            "actionable_items": "Review and respond to this client email.",
            "is_expense": False,
            "is_portal_update": False,
            "needs_hitl_check": False,
            "whitelist_override": True,
        }
    # =====================================================================

    # --- STANDARD PRE-FILTER (unknown senders ONLY — all whitelist/override checks already done above) ---
    # IMPORTANT: We only apply shortcut rules to truly unknown senders.
    # Any real email with a question, attachment, or substantial body goes to AI triage.
    # This prevents genuine "Hi, I need your help" short emails from being auto-archived.
    if has_attachments:
        return None  # Always let AI handle emails with attachments
    # If the email has a question mark anywhere, treat it as a genuine inquiry — never pre-filter
    if "?" in snippet or "?" in subject:
        return None
    # If email body is substantial, send to AI for proper categorisation
    if len(snippet.split()) > 10:
        return None

    # 1. Obvious Spam (Tier 5)
    spam_keywords = [
        "unsubscribe",
        "no-reply",
        "promotion",
        "marketing",
        "offering 50%",
        "lottery",
    ]
    if any(k in snippet for k in spam_keywords) or any(
        k in subject for k in spam_keywords
    ):
        return {
            "tier": 5,
            "reason": "Automated rule: Spam/Marketing keywords detected.",
            "actionable_items": "None",
            "is_expense": False,
        }

    # 2. Automated Portal/System Updates (Tier 4)
    portal_keywords = [
        "notification",
        "digest",
        "daily update",
        "system alert",
        "password reset",
        "verification code",
    ]
    if any(k in subject for k in portal_keywords):
        return {
            "tier": 4,
            "reason": "Automated rule: System notification detected.",
            "is_portal_update": True,
            "actionable_items": "None",
        }

    # 3. Simple Politeness (Tier 4)
    if len(snippet.split()) < 5 and any(
        k in snippet for k in ["thanks", "thank you", "ok", "got it"]
    ):
        return {
            "tier": 4,
            "reason": "Automated rule: Short polite reply.",
            "actionable_items": "None",
        }

    return None


def triage_email(email_content, client_context=None):
    """Categorizes the email into one of 5 Tiers using Gemini with client context."""
    try:
        # --- LAYER 0: PRE-FILTER (ZERO COST) ---
        pre_triage = pre_triage_rules(email_content)
        if pre_triage:
            return pre_triage

        # --- LAYER 1: GEMINI (PAID/LIMITED) ---
        client = get_gemini_client()
        if not client:
            return {"tier": 5, "reason": "Gemini client not initialized"}

        context_str = (
            f"EXISTING CLIENT INFO: {client_context}"
            if client_context
            else "NEW CONTACT (Not in Master List)."
        )

        prompt = f"""
        Analyze the following email and categorize it into exactly ONE of the following Tiers.
        
        {context_str}

        TIERS (CHERRY'S REFINED MAP):
        Tier 1: Active Clients / Whitelist. (Coiera, Angelo, David, John Watts). Action: STAY IN INBOX. DO NOT auto-draft unless Steve explicitly asks.
        Tier 2: Govt / Assoc / Special Shields (ATO, ASIC, IPA, IFPA, NDIS, Stripe, Cloudoffis). Action: STAY IN INBOX. DO NOT auto-draft unless asked.
        Tier 3: Suppliers / General / Subscriptions (Superloop, NAB, ANZ, Telstra, AppSumo, Whapi, Linkedin, SimpleFund). Action: Log to Govt_Assoc_Log & Archive.
        Tier 4: Portal Digests / Routine Updates (Suitedash, Portal notifications). Action: Log to Portal_Updates & Archive.
        Tier 5: Spam / Marketing / Noise. Action: Trash.

        IMPORTANT - NEW CONTACTS:
        - If sender is NOT in client whitelist AND email contains business inquiry, potential work, or questions about services → Set "is_new_lead": true
        - If "is_new_lead": true, also provide "lead_notes": brief summary of what they're asking for
        - If existing client → Set "is_existing_client": true
        
        ACTIONABLE ITEMS:
        Specifically extract what needs to be done (e.g., "Reply about SMSF doc", "Check invoice total").
        For Tier 1 OR new leads, provide a high-quality draft (only for clients, not for Tier 2).
        
        INCLUSIVE DESIGN & CULTURE:
        Your analysis must be empathetic and culturally aware. When identifying actionable items, 
        consider the human context and use accessible language.

        EMAIL CONTENT:
        Subject: {email_content.get("subject")}
        Snippet: {email_content.get("snippet")}
        
        RESPONSE FORMAT (Strict JSON):
        {{
          "tier": 1, 
          "reason": "String reason", 
          "actionable_items": "Detailed action",
          "is_expense": false,
          "is_portal_update": false,
          "needs_hitl_check": false,
          "is_new_lead": false,
          "is_existing_client": false,
          "lead_notes": "",
          "expense_data": {{
            "vendor": "Name",
            "amount": "$",
            "due_date": "YYYY-MM-DD"
          }}
        }}
        """

        # Use OpenRouter with gemini-2.5-flash-exp:free to avoid deprecation
        or_response = get_openrouter_response(
            prompt,
            model="google/gemini-2.5-flash-exp:free",
            sys_prompt="You are an email triage AI. Return only valid JSON.",
            json_mode=True,
        )
        if or_response:
            try:
                return json.loads(or_response)
            except Exception:
                pass
        # Fallback: try native Gemini client
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )

        response_text = response.text.strip() if response and response.text else "{}"
        triage_data = json.loads(response_text)
        return triage_data
    except Exception as e:
        logger.error(f"GEMINI TRIAGE FAIL: {e}. Falling back to Ollama...")

        # --- LAYER 2: OLLAMA FALLBACK (ZERO COST) ---
        fallback_prompt = (
            email_content.get("subject", "") + " " + email_content.get("snippet", "")
        )
        ollama_res = get_ollama_response(fallback_prompt, json_mode=True)
        if ollama_res:
            try:
                return json.loads(ollama_res)
            except Exception:
                pass

        return {"tier": 5, "reason": f"AI Error: {str(e)}"}


def _draft_response_openrouter(
    email_content: dict, tier: int, historical_context="", client_info=None
) -> str:
    """Generate draft using OpenRouter API."""
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        return None

    subject = email_content.get("subject", "")
    snippet = email_content.get("snippet", "")

    prompt = f"""You are a professional email assistant. Generate a brief, professional response to this email.

Subject: {subject}
From: {email_content.get("sender", "")}

Message snippet: {snippet}

Generate a concise (2-3 sentences), professional response draft."""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {openrouter_key}",
                "HTTP-Referer": "backpocket.ai",
            },
            json={
                "model": "openrouter/auto",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 200,
            },
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()
        draft = (
            result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        )
        if draft:
            logger.info(f"✓ OpenRouter draft: {draft[:50]}...")
            return draft
    except Exception as e:
        logger.warning(f"OpenRouter failed: {e}")
        return None


def draft_response(email_content, tier, historical_context="", client_info=None):
    """Generates a professional draft response using cost-optimized ML router.

    Strategy:
    1. Low-entropy emails: Use template
    2. Medium-entropy: Use Ollama (local, no cost)
    3. High-entropy: Use OpenRouter/Gemini
    """
    # Cost optimization: Check if full AI is needed
    entropy = calculate_entropy(
        email_content.get("subject", "") + " " + email_content.get("snippet", "")
    )
    logger.info(f"📊 Email entropy: {entropy} (Tier {tier})")

    if not _should_use_full_ai(email_content, tier) and entropy < 3.0 and tier != 1:
        # Simple template for low-complexity emails (but NOT for Tier 1 important clients)
        logger.info("💰 Using template (low entropy, saves API cost)")
        subject = email_content.get("subject", "")
        return f"Thanks for reaching out. I'll review this and get back to you shortly."

    # Try OpenRouter first (better quota)
    openrouter_draft = _draft_response_openrouter(
        email_content, tier, historical_context, client_info
    )
    if openrouter_draft:
        return openrouter_draft

    # Fall back to Ollama (local, no quota)
    try:
        ollama_res = get_ollama_response(
            email_content.get("subject", "") + " " + email_content.get("snippet", "")
        )
        if ollama_res and ollama_res != "Error generating draft.":
            logger.info("💾 Used Ollama for draft (local)")
            return ollama_res
    except Exception as e:
        logger.warning(f"Ollama failed: {e}")

    # Fall back to Gemini (may be rate limited)
    try:
        client = get_gemini_client()
        if not client:
            return "Gemini not initialized"

        client_note = (
            f"CLIENT BACKGROUND: {client_info.get('background_info')}"
            if client_info
            else "NEW CONTACT."
        )
        client_name = client_info.get("first_name", "there") if client_info else "there"

        # Load Steve's Style Guide from file
        style_guide = ""
        style_path = os.path.join("docs", "CHERRY_STYLE.txt")
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                style_guide = f.read()

        # Load corrections history for learning (especially for Tier 1 clients)
        corrections_context = ""
        sender_instructions = ""
        if tier in ["1", 1]:
            try:
                import services.database as db

                # Get corrections relevant to this sender or subject
                email_sender = email_content.get("sender", "")
                email_subject = email_content.get("subject", "")
                relevant_corrections = db.get_learned_patterns(
                    sender_email=email_sender, subject=email_subject, limit=5
                )
                if relevant_corrections:
                    corrections_context = "\n\nCHERRY'S PREVIOUS CORRECTIONS FOR SIMILAR EMAILS (learn her preferences):\n"
                    for c in relevant_corrections:
                        corrections_context += (
                            f"- Feedback: {c.get('feedback', 'N/A')}\n"
                        )
                        corrections_context += f"  Original draft: {c.get('original_draft', '')[:150]}...\n"
                        corrections_context += (
                            f"  Corrected to: {c.get('corrected_draft', '')[:150]}...\n"
                        )
                else:
                    # Fall back to recent corrections if no relevant ones
                    recent_corrections = db.get_corrections(limit=3)
                    if recent_corrections:
                        corrections_context = (
                            "\n\nCHERRY'S RECENT PREFERENCES (general):\n"
                        )
                        for c in recent_corrections[:3]:
                            corrections_context += f"- {c.get('feedback', 'N/A')}\n"
            except Exception as e:
                logger.warning(f"Could not load corrections: {e}")

        # Get historical email context for Tier 1 (existing clients)
        email_sender = email_content.get("sender", "")
        if tier in ["1", 1] and email_sender and not historical_context:
            try:
                from services.gmail import get_historical_context

                historical_context = get_historical_context(email_sender, max_results=3)
            except Exception as e:
                logger.warning(f"Could not load historical context: {e}")

        # Get sender-specific instructions for Twin
        sender_instructions = ""
        if email_sender:
            try:
                import services.database as db

                sender_info = db.get_sender_instruction(email_sender)
                if sender_info and sender_info.get("instructions"):
                    sender_instructions = f"\n\nSPECIAL INSTRUCTIONS FOR THIS SENDER:\n{sender_info['instructions']}\n"
                    if sender_info.get("category"):
                        sender_instructions += f"Category: {sender_info['category']}\n"
            except Exception as e:
                logger.warning(f"Could not load sender instructions: {e}")

        # Extract sender's name from email for personalization
        sender_info = email_content.get("sender", "")
        sender_name = "there"
        if sender_info and "@" in sender_info:
            # Try to get name from sender info - could be "Name <email>" format
            from_name = email_content.get("from_name", "")
            if from_name:
                # Extract first name
                name_parts = from_name.strip().split()
                if name_parts:
                    sender_name = name_parts[0]

        # Generate suggested actions based on sender instructions
        suggested_actions = []
        if sender_instructions:
            # Parse instructions to find action keywords
            inst_text = sender_instructions.lower()
            if (
                "builder tracker" in inst_text
                or "builder" in sender_info.get("category", "").lower()
            ):
                suggested_actions.append(
                    {
                        "action": "add_to_sheet",
                        "sheet": "Builder_Tracker",
                        "label": "Add to Builder Tracker",
                    }
                )
            if "compare quotes" in inst_text:
                suggested_actions.append(
                    {"action": "compare_quotes", "label": "Compare Quotes"}
                )
            if "cost-saving" in inst_text or "insight" in inst_text:
                suggested_actions.append(
                    {"action": "provide_insight", "label": "Provide Cost Insights"}
                )

        prompt = f"""
        You are Steve, founder of BackPocket. Rewrite this email AS IF YOU wrote it.
        
        MANDATORY SELF-CHECK RULES:
        - Only write facts from the email, don't hallucinate
        - If unsure about something, ask the user
        - Don't make up dates, prices, or details
        - Cite "the email says..." when referring to specific info
        
        MANDATORY WRITING RULES (follow exactly):
        1. ALWAYS personalize with first name: Start with "Hi {sender_name}," if you know their name
        2. Start with actual message - NO "Subject:", NO intro like "Thanks for..."
        3. Use FIRST PERSON: "I" or "We" - NEVER "Steve finds", NEVER "BackPocket Twin"  
        4. Maximum 4 sentences
        5. END with EXACTLY: "Talk soon, Steve" or "Thanks, Steve" (pick one based on tone)
        6. NO other signature, NO title, NO "AI", NO robot mention
        
        {corrections_context}
        {sender_instructions}
        
        ORIGINAL EMAIL:
        Subject: {email_content.get("subject")}
        From: {email_content.get("sender", "")}
        Body: {email_content.get("snippet")}
        
        Rewrite Steve's reply (use their first name if known):
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        response_text = response.text.strip() if response and response.text else ""

        # Return dict with draft AND suggested actions (human must approve actions)
        return {
            "draft": response_text,
            "suggested_actions": suggested_actions,
            "sender_instructions": sender_info.get("instructions", "")
            if sender_info
            else "",
        }
    except Exception as e:
        logger.error(f"GEMINI DRAFT FAIL: {e}. Falling back to Ollama...")
        fallback_prompt = (
            email_content.get("subject", "") + " " + email_content.get("snippet", "")
        )
        ollama_res = get_ollama_response(fallback_prompt)
        if ollama_res:
            return ollama_res
        return "Error generating draft."


def refine_draft(email_content, original_draft, feedback):
    """Refines an existing draft based on founder's feedback."""
    prompt = f"Refine: {original_draft}\nFeedback: {feedback}"
    try:
        client = get_gemini_client()
        if not client:
            return "Gemini client not initialized."

        # Load previous corrections to learn Steve's preferences
        corrections_learn = ""
        try:
            import services.database as db

            recent = db.get_corrections(limit=5)
            if recent:
                corrections_learn = "\n\nCHERRY'S PAST CORRECTION PATTERNS (IMPORTANT - learn what she likes/dislikes):\n"
                for c in recent[:5]:
                    corrections_learn += f"- Feedback: {c.get('feedback', '')}\n"
                    corrections_learn += (
                        f"  Corrected: {c.get('corrected_draft', '')[:100]}...\n"
                    )
        except:
            pass

        prompt = f"""
        Refine this email draft based on feedback. Fix it to sound like Steve wrote it.
        
        MANDATORY RULES:
        - Use "I" or "We" - NEVER "BackPocket Twin" or "Steve finds"
        - End with EXACTLY: "Talk soon, Steve" or "Thanks, Steve"
        - No extra signatures or titles
        - Personalize with recipient's first name if you know it
        
        {corrections_learn}
        
        FOUNDER'S FEEDBACK (MUST FOLLOW THIS):
        "{feedback}"

        ORIGINAL DRAFT:
        {original_draft}

        Rewrite following the feedback:
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )

        response_text = response.text.strip() if response and response.text else ""
        if not response_text:
            # Try Ollama as fallback
            ollama_res = get_ollama_response(prompt)
            if ollama_res:
                response_text = ollama_res

        return response_text if response_text else original_draft
    except Exception as e:
        logger.error(f"Error in refine_draft: {e}")
        # Try Ollama as fallback
        ollama_res = get_ollama_response(prompt)
        if ollama_res:
            return ollama_res
        return original_draft


def batch_triage_emails(emails_list: list):
    """
    LAYER 1: Batch Triage via Gemini (batch_triage_emails).
    Triages multiple emails in a SINGLE LLM CALL.
    Strictly maps results by message_id.
    """
    if not emails_list:
        logger.info("Batch triage called with empty list.")
        return {}

    try:
        client = get_gemini_client()
        if not client:
            return {
                e.get("id"): {"tier": 5, "reason": "Gemini not initialized"}
                for e in emails_list
            }

        # Stringify the batch for the prompt
        emails_str = ""
        for email in emails_list:
            emails_str += f"--- MESSAGE_ID: {email.get('id')} ---\nSubject: {email.get('subject')}\nSnippet: {email.get('snippet')}\n\n"

        prompt = f"""
        You are the Chief Architect AI for BackPocketSystem.io. 
        Analyze the following batch of {len(emails_list)} emails and triage them.
        
        INCLUSIVE DESIGN & CULTURE:
        Your analysis must be empathetic and culturally aware. When identifying actionable items, 
        consider the human context and use accessible language.

    - TIER 1 (PRIORITY): Active Clients (Gino Coiera, Angelo Memmolo, David). Action: STAY IN INBOX.
    - TIER 2 (GOVT / ASSOC / SHIELDS): ATO, ASIC, IPA, IFPA, NDIS, Stripe, Cloudoffis. Action: STAY IN INBOX.
    - TIER 3 (SUPPLIERS / GENERAL): Superloop, NAB, ANZ, Telstra, AppSumo, Whapi, Linkedin, SimpleFund. Action: Log & Archive.
    - TIER 4 (PORTAL / UPDATES / DIGESTS): Suitedash Digests. Action: Log & Archive.
    - TIER 5 (SPAM): Anything else (Marketing, Promo, Unsubscribe). Action: Trash.

        EMAILS TO ANALYZE:
        {emails_str}

        RESPONSE FORMAT (Strict JSON Map):
        You MUST return a JSON object where each key is the MESSAGE_ID provided above.
        The value for each key must be the triage data object.
        
        Example:
        {{
          "msg_id_abc": {{
            "tier": 1, 
            "reason": "...", 
            "actionable_items": "...",
            "is_expense": false,
            "is_portal_update": false
          }}
        }}
        """

        # Use OpenRouter with gemini-2.5-flash-exp:free to avoid deprecation
        or_response = get_openrouter_response(
            prompt,
            model="google/gemini-2.5-flash-exp:free",
            sys_prompt="You are a batch email triage AI. Return only valid JSON.",
            json_mode=True,
        )
        if or_response:
            try:
                return json.loads(or_response)
            except Exception:
                pass
        # Fallback: try native Gemini client
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )

        response_text = response.text.strip() if response and response.text else "{}"
        batch_results = json.loads(response_text)
        return batch_results
    except Exception as e:
        logger.error(
            f"GEMINI BATCH FAIL: {e}. Falling back to individual Ollama triage..."
        )

        fallback_results = {}
        for email in emails_list:
            msg_id = email.get("id")
            logger.info(
                f"💾 LAYER 2 FALLBACK: Triaging {msg_id} individually via Ollama..."
            )

            # Reuse the triage prompt logic for individual emails
            prompt = f"""
            Analyze the following email and categorize it into exactly ONE Tier.
            
            TIERS (CHERRY'S HANDWRITTEN MAP):
            Tier 1: Active Clients.
            Tier 2: Govt / Assoc (ATO, ASIC, IPA, IPFA, Auditors Institute).
            Tier 3: Suppliers / General (Stripe, Hubspot, Google, Intuit, Xero).
            Tier 4: Portals / Updates (Daily Digest, Business 1300).
            Tier 5: Spam.

            RESPONSE FORMAT (Strict JSON):
            {{
              "tier": 1, 
              "reason": "String reason", 
              "actionable_items": "...",
              "is_expense": false,
              "is_portal_update": false
            }}

            EMAIL CONTENT:
            Subject: {email.get("subject")}
            Snippet: {email.get("snippet")}
            """

            ollama_res = get_ollama_response(prompt, json_mode=True)
            if ollama_res:
                try:
                    fallback_results[msg_id] = json.loads(ollama_res)
                except Exception as parse_err:
                    logger.error(f"❌ OLLAMA PARSE FAIL for {msg_id}: {parse_err}")
                    fallback_results[msg_id] = {
                        "tier": 5,
                        "reason": "Ollama parse error",
                    }
            else:
                fallback_results[msg_id] = {
                    "tier": 5,
                    "reason": "Ollama connection/timeout error",
                }

        return fallback_results
