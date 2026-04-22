from typing import Dict, Any
import logging
from services.coach.authority_check import scan_authority
from services.coach.clarity_check import scan_clarity
from services.coach.empathy_check import scan_empathy

logger = logging.getLogger(__name__)

def review_draft(draft_text: str) -> Dict[str, Any]:
    """
    Main coach logic: runs Empathy, Authority, and Clarity scanners.
    Generates a combined score and feedback.
    """
    if not draft_text or not draft_text.strip():
        return {
            "score": 0,
            "feedback": "Draft is empty.",
            "tone": "N/A",
            "passed": False,
            "power_version": None
        }

    authority_res = scan_authority(draft_text)
    clarity_res = scan_clarity(draft_text)
    empathy_res = scan_empathy(draft_text)

    # Average score
    overall_score = int((authority_res["score"] + clarity_res["score"] + empathy_res["score"]) / 3)

    feedback_items = []
    for iss in authority_res.get("issues", []):
        feedback_items.append(iss["suggestion"])
    for iss in clarity_res.get("issues", []):
        feedback_items.append(iss["suggestion"])
    for iss in empathy_res.get("issues", []):
        feedback_items.append(iss["suggestion"])

    feedback_text = " ".join(feedback_items) if feedback_items else "Looking good! Very confident, clear, and empathetic."

    tone = "Confident & Clear"
    if overall_score < 70:
        tone = "Needs Improvement"
    elif overall_score < 85:
        tone = "Almost There"

    # In a real setup, we'd call an LLM to generate the "Power Version" here if score < 100
    power_version = None
    if overall_score < 90:
        power_version = _generate_power_version_stub(draft_text)

    return {
        "score": overall_score,
        "tone": tone,
        "feedback": feedback_text,
        "passed": overall_score >= 80,
        "power_version": power_version,
        "breakdown": {
            "authority": authority_res["score"],
            "clarity": clarity_res["score"],
            "empathy": empathy_res["score"]
        }
    }

def _generate_power_version_stub(original: str) -> str:
    """Fallback stub for power version. Would be replaced by actual LLM rewrite."""
    # We could plug into services.gemini.get_openrouter_response here if we wanted.
    # For now, just return a sanitized version (stub).
    return "Hi there,\n\n" + original.replace("I think ", "").replace("maybe ", "") + "\n\nPlease let me know your thoughts.\n\nCheers,"
