import re
from typing import Dict, Any

def scan_clarity(text: str) -> Dict[str, Any]:
    """
    Scans a draft for clarity:
    - Checks if sentences are too long.
    - Checks for a clear Call To Action (CTA).
    """
    issues = []
    
    # Check sentence length (rough heuristic: > 25 words is too long)
    sentences = re.split(r'[.!?]+', text)
    long_sentences = []
    for s in sentences:
        words = s.strip().split()
        if len(words) > 25:
            long_sentences.append(s.strip())
            
    if long_sentences:
        issues.append({
            "type": "long_sentences",
            "count": len(long_sentences),
            "suggestion": "Some sentences are very long. Try breaking them up to improve readability."
        })
        
    # Check for CTA presence (question mark or specific action words)
    cta_words = ["please let me know", "could you", "call me", "reply", "can we", "?", "let's schedule", "sign"]
    has_cta = any(cta in text.lower() for cta in cta_words)
    
    if not has_cta:
        issues.append({
            "type": "missing_cta",
            "suggestion": "The draft lacks a clear Call To Action. End with a specific request or question."
        })
        
    deduction = 0
    if long_sentences:
        deduction += 15
    if not has_cta:
        deduction += 20
        
    return {
        "score": 100 - deduction,
        "issues": issues,
        "passed": len(issues) == 0
    }
