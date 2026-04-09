import os
import requests
import logging
import json

logger = logging.getLogger(__name__)

def run_self_audit():
    """Reads all project files and feeds them to Ollama for a 'Twin Audit'."""
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/api/generate")
    model = os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b")
    
    # 1. READ CORE SYSTEM FILES
    files_to_audit = [
        "main.py",
        "services/gemini.py",
        "services/google_sheets.py",
        "services/gmail.py",
        "services/whapi.py"
    ]
    
    codebase_summary = ""
    for f in files_to_audit:
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as file:
                codebase_summary += f"\n\n--- FILE: {f} ---\n{file.read()[:2000]}..." # Limit for Ollama context

    prompt = f"""
    You are the 'BackPocket Digital Twin Auditor'.
    
    SYSTEM DIRECTORY AUDIT:
    {codebase_summary}
    
    CHALLENGE: 
    Cherry wants her Twin to be smarter, faster, and zero-cost.
    Based on the code above:
    1. Identify any potential bugs or 'stuck' points.
    2. Suggest one improvement to the dashboard to make it more mobile-friendly.
    3. How can we make the triage logic 'Cherry-Identity' compliant?
    
    Think like a world-class CTO for a small business.
    Return your report in a warm, helpful tone.
    """
    
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        logger.info(f"💾 LOCAL AUDIT: Generating self-report via Ollama ({model})...")
        response = requests.post(ollama_url, json=payload, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        raw_text = data.get("response", "")
        
        # Clean <think> tags if DeepSeek
        import re
        clean_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()
        
        # Save results to docs for permanent reference
        with open("docs/LATEST_LOCAL_AUDIT.md", "w", encoding="utf-8") as f:
            f.write(f"# 🕵️ LOCAL OLLAMA AUDIT REPORT\nDate: {json.dumps(str(os.times()))}\n\n{clean_text}")
            
        return clean_text
    except Exception as e:
        logger.error(f"❌ LOCAL AUDIT FAILED: {e}")
        return f"Self-audit failed: {str(e)}"
