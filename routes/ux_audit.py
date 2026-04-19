"""
UX Auditor — AI-powered heuristic evaluation endpoint.

POST /api/ux/audit
  - Accepts a screen description (text) or image_base64
  - Evaluates against Nielsen's 10 Usability Heuristics
  - Returns structured JSON: {issues, score, fixes}

POST /api/ux/audit-code
  - Accepts raw Dart UI code snippet
  - Returns: {issues, refactored_snippet, explanation}
"""

import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ux", tags=["ux-audit"])

NIELSENS_HEURISTICS = """
1. Visibility of system status
2. Match between system and the real world
3. User control and freedom
4. Consistency and standards
5. Error prevention
6. Recognition rather than recall
7. Flexibility and efficiency of use
8. Aesthetic and minimalist design
9. Help users recognise, diagnose, and recover from errors
10. Help and documentation
"""

_AUDIT_SYSTEM = (
    "You are a Senior UX Designer and Flutter accessibility expert. "
    "You evaluate mobile app UIs against Nielsen's 10 Usability Heuristics "
    "with specific focus on Australian tradie/SME users (low tech literacy, "
    "often used outdoors, one hand on phone). Be direct and actionable."
)

_CODE_SYSTEM = (
    "You are a Flutter/Dart UI engineer and accessibility expert. "
    "Identify usability anti-patterns in Dart widget code and provide "
    "a refactored snippet. Focus on: tap target sizes (min 48x48dp), "
    "contrast ratios, loading states, error messages, and semantic labels."
)


class AuditRequest(BaseModel):
    screen_name: str
    description: str
    image_base64: Optional[str] = None
    user_type: str = "tradie"


class CodeAuditRequest(BaseModel):
    screen_name: str
    dart_code: str
    context: Optional[str] = None


@router.post("/audit")
async def audit_screen(req: AuditRequest):
    """Run Nielsen heuristic evaluation on a screen description."""
    from services.gemini import get_openrouter_response

    prompt = f"""You are auditing the "{req.screen_name}" screen of BackPocket OS,
a mobile business management app for Australian {req.user_type}s.

SCREEN DESCRIPTION:
{req.description}

NIELSEN'S 10 HEURISTICS:
{NIELSENS_HEURISTICS}

Task: Identify exactly 3 critical usability issues (most impactful first).
For each issue return:
- heuristic_number: (1-10)
- heuristic_name: (e.g. "Error prevention")
- issue: one sentence describing the problem
- severity: "critical" | "major" | "minor"
- fix: one concrete, specific improvement (e.g. "Add a confirmation dialog before deleting a lead")

Also return:
- ux_score: integer 0-100 (current usability quality)
- summary: one sentence overall verdict

Return ONLY valid JSON with this structure:
{{
  "screen": "{req.screen_name}",
  "ux_score": 75,
  "summary": "...",
  "issues": [
    {{"heuristic_number": 5, "heuristic_name": "Error prevention", "issue": "...", "severity": "critical", "fix": "..."}}
  ]
}}"""

    try:
        result = get_openrouter_response(
            prompt,
            model="openrouter/auto",
            sys_prompt=_AUDIT_SYSTEM,
            json_mode=True,
        )
        if result:
            import json
            return {"status": "success", "audit": json.loads(result) if isinstance(result, str) else result}
        return {"status": "error", "message": "AI unavailable"}
    except Exception as e:
        logger.error(f"UX audit error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/audit-code")
async def audit_dart_code(req: CodeAuditRequest):
    """Audit a Dart widget for usability issues and return refactored code."""
    from services.gemini import get_openrouter_response

    prompt = f"""Audit this Flutter/Dart code for the "{req.screen_name}" screen.
{f"Context: {req.context}" if req.context else ""}

DART CODE:
```dart
{req.dart_code}
```

Find up to 3 usability/accessibility issues. For each:
- issue: what's wrong
- fix: specific code change

Then provide a complete refactored version of the code with all fixes applied.

Return ONLY valid JSON:
{{
  "screen": "{req.screen_name}",
  "issues": [{{"issue": "...", "fix": "..."}}],
  "refactored_code": "...full dart code..."
}}"""

    try:
        result = get_openrouter_response(
            prompt,
            model="openrouter/auto",
            sys_prompt=_CODE_SYSTEM,
            json_mode=True,
        )
        if result:
            import json
            return {"status": "success", "audit": json.loads(result) if isinstance(result, str) else result}
        return {"status": "error", "message": "AI unavailable"}
    except Exception as e:
        logger.error(f"UX code audit error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/audit-all")
async def audit_all_screens():
    """Run heuristic audit on all 11 BackPocket screens in one batch."""
    screens = [
        ("Dashboard", "Shows live stats: pending emails, pipeline value, payment status. Has quick-action buttons. Amber/dark theme."),
        ("Inbox", "List of pending emails needing approval. Each card shows sender, subject, AI draft preview, Approve/Revise buttons."),
        ("Construction", "Tabs: Leads / Quotes / Payments. Cards show job type, location, budget, status badge. FAB to create new lead."),
        ("Documents", "File upload + AI analysis. Shows uploaded docs with analysis results."),
        ("Marketing", "GBP post / Facebook / Instagram generators. Text fields for job description + suburb. Generated content display."),
        ("Twin Chat", "Chat interface with BackPocket AI twin. Message bubbles, input field, send button."),
        ("Voice Input", "Large mic button, live transcript display, voice command examples list."),
        ("Vision Chat", "Camera/gallery image picker + AI material assessment. Shows damage report."),
        ("Instructions", "List of saved AI behaviour rules. Add/edit/delete instructions by category."),
        ("Settings", "Server URL, API key, BYOK sovereign engine section, About info."),
        ("Voice Help", "Reference card showing all available voice commands by screen."),
    ]

    from services.gemini import get_openrouter_response
    import json

    results = []
    for name, desc in screens:
        prompt = f"""Audit "{name}" screen of BackPocket OS (mobile app for Australian tradies).
Description: {desc}
Nielsen heuristics: {NIELSENS_HEURISTICS}
Return JSON: {{"screen":"{name}","ux_score":0-100,"top_issue":"one sentence","fix":"one sentence"}}"""
        try:
            result = get_openrouter_response(prompt, model="openrouter/auto", sys_prompt=_AUDIT_SYSTEM, json_mode=True)
            if result:
                data = json.loads(result) if isinstance(result, str) else result
                results.append(data)
            else:
                results.append({"screen": name, "ux_score": None, "top_issue": "AI unavailable", "fix": ""})
        except Exception as e:
            results.append({"screen": name, "error": str(e)})

    avg_score = sum(r.get("ux_score", 0) or 0 for r in results) / len(results)
    return {
        "status": "success",
        "overall_score": round(avg_score),
        "screens_audited": len(results),
        "results": results,
    }
