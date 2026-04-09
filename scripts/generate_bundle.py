import os
import glob

def generate_audit_bundle():
    """Generates a single block of text containing all code, to be fed to Ollama."""
    files_to_bundle = [
        "main.py",
        "services/*.py",
        "static/app.js",
        "static/index.html",
        "docs/ERROR_LOG.md",
        "LAUNCH_BACKPOCKET_TWIN.bat"
    ]
    
    all_content = ""
    for pattern in files_to_bundle:
        for file_path in glob.glob(pattern):
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        all_content += f"\n\n--- START FILE: {file_path} ---\n"
                        all_content += f.read()
                        all_content += f"\n--- END FILE: {file_path} ---\n"
                except: continue

    audit_prompt = f"""
### SYSTEM AUDIT REQUEST FOR BACKPOCKET TWIN (Brain 1 LAB)
You are an expert system auditor for the BackPocket team. Cherry is your founder.

BELOW IS THE ENTIRE SOURCE CODE FOR THE BACKPOCKET TWIN:
{all_content}

--- AUDIT OBJECTIVES ---
1.  **Code Health**: Identify any potential logic loops or crashing points in 'main.py' or the services.
2.  **Cost Efficiency**: Review 'gemini.py' and suggest where we can use local Ollama models instead of high-cost Gemini Flash calls to save money.
3.  **Identity Compliance**: Ensure the 'Cherry Style' (warm, helpful, concise) is defined well in the prompt logic.
4.  **UI/UX**: Review 'app.js' and 'index.html' to ensure the dashboard feels premium and 'Glassmorphic'.

Provide a concise, numbered list of improvements.
"""
    
    with open("docs/MASTER_AUDIT_PROMPT.txt", "w", encoding="utf-8") as f:
        f.write(audit_prompt)
        
    print("✅ Generated docs/MASTER_AUDIT_PROMPT.txt. Copy its content to Ollama!")

if __name__ == "__main__":
    generate_audit_bundle()
