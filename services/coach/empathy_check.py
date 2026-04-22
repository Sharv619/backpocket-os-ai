import re
from typing import Dict, Any

WARM_OPENINGS = [
    r"hi", r"hello", r"hope you", r"thanks for", r"great to hear"
]

COLD_PHRASES = [
    r"as per my previous",
    r"per our conversation",
    r"it has come to my attention",
    r"please be advised"
]

def scan_empathy(text: str) -> Dict[str, Any]:
    """
    Scans a draft for an empathetic, human tone.
    """
    text_lower = text.lower()
    issues = []
    deduction = 0
    
    # Check for warm opening (first 50 chars)
    intro = text_lower[:50]
    has_warm_opening = any(re.search(r'\b' + warm + r'\b', intro) for warm in WARM_OPENINGS)
    
    if not has_warm_opening:
        issues.append({
            "type": "cold_opening",
            "suggestion": "Consider starting with a warmer greeting (e.g., 'Hi [Name]', 'Hope you're having a good week')."
        })
        deduction += 10
        
    # Check for robotic/overly formal phrases
    for cold in COLD_PHRASES:
        if re.search(r'\b' + cold + r'\b', text_lower):
            issues.append({
                "type": "robotic_language",
                "phrase": cold,
                "suggestion": f"The phrase '{cold}' can sound robotic or passive-aggressive. Try a more conversational alternative."
            })
            deduction += 15
            
    return {
        "score": max(0, 100 - deduction),
        "issues": issues,
        "passed": len(issues) == 0
    }
