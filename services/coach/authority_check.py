import re
from typing import Dict, Any

WEAK_PHRASES = [
    r"i think",
    r"maybe",
    r"sorry to bother you",
    r"just wanted to",
    r"i might be wrong but",
    r"does that make sense",
    r"kind of",
    r"sort of"
]

def scan_authority(text: str) -> Dict[str, Any]:
    """
    Scans a draft for weak language that undermines authority.
    Returns a score deduction and a list of suggestions.
    """
    text_lower = text.lower()
    found_issues = []
    
    for phrase in WEAK_PHRASES:
        matches = re.finditer(r'\b' + phrase + r'\b', text_lower)
        for match in matches:
            found_issues.append({
                "phrase": match.group(),
                "suggestion": f"Avoid using '{match.group()}' to sound more confident and decisive."
            })
            
    # Calculate score deduction (max -30)
    deduction = min(len(found_issues) * 10, 30)
    
    return {
        "score": 100 - deduction,
        "issues": found_issues,
        "passed": len(found_issues) == 0
    }
