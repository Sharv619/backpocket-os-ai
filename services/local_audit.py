import os
import re
import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Free, 65k context, strong reasoning — no Ollama required
AUDIT_MODEL = os.getenv(
    "OPENROUTER_AUDIT_MODEL", "meta-llama/llama-3.3-70b-instruct:free"
)
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"


def run_self_audit():
    """Reads core project files and sends them to OpenRouter for a Twin Audit.
    Replaces the previous Ollama/deepseek implementation.
    """
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        return "Self-audit unavailable: OPENROUTER_API_KEY not set."

    # Read core files (cap each at 2000 chars to stay within context)
    files_to_audit = [
        "main.py",
        "services/gemini.py",
        "services/google_sheets.py",
        "services/gmail.py",
        "services/whapi.py",
    ]

    codebase_summary = ""
    for path in files_to_audit:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                snippet = fh.read()[:2000]
            codebase_summary += f"\n\n--- FILE: {path} ---\n{snippet}...(truncated)"

    prompt = (
        "You are the BackPocket Digital Twin Site Manager — a world-class CTO advisor "
        "for a small Australian accounting and trades business.\n\n"
        "SYSTEM CODE SNAPSHOT:\n"
        f"{codebase_summary}\n\n"
        "YOUR AUDIT TASKS:\n"
        "1. Identify any potential bugs or stuck points in the code.\n"
        "2. Suggest one improvement to make the dashboard more mobile-friendly.\n"
        "3. How can the email triage logic be made more 'Steve-Identity' compliant "
        "(i.e. better reflecting Steve's personal client relationships and tone)?\n\n"
        "Be direct, warm, and practical. Keep each point concise."
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://backpocket.os",
        "X-Title": "BackPocket OS",
        "Content-Type": "application/json",
    }
    payload = {
        "model": AUDIT_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful CTO site_manager. Be concise."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 1200,
    }

    try:
        logger.info(f"AUDIT: Requesting self-report via OpenRouter ({AUDIT_MODEL})...")
        response = requests.post(
            OPENROUTER_BASE_URL, headers=headers, json=payload, timeout=60
        )
        response.raise_for_status()

        data = response.json()
        raw_text = data["choices"][0]["message"]["content"]

        # Strip any residual <think> tags (some models include them)
        clean_text = re.sub(
            r"<think>.*?</think>", "", raw_text, flags=re.DOTALL
        ).strip()

        # Persist to docs/
        os.makedirs("docs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open("docs/LATEST_LOCAL_AUDIT.md", "w", encoding="utf-8") as fh:
            fh.write(
                f"# BackPocket Twin Audit Report\n"
                f"**Date:** {timestamp}  |  **Model:** {AUDIT_MODEL}\n\n"
                f"{clean_text}"
            )

        logger.info("AUDIT: Complete — saved to docs/LATEST_LOCAL_AUDIT.md")
        return clean_text

    except Exception as e:
        logger.error(f"AUDIT FAILED: {e}")
        return f"Self-audit failed: {str(e)}"
