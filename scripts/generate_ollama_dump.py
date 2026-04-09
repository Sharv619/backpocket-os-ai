import os

def generate_ollama_dump():
    """Generates a single, massive text file containing all the critical code for BackPocket."""
    target_files = [
        "PROJECT_CONTEXT.md",
        "docs/TWIN_DIAGNOSIS_SOP.md",
        "main.py",
        "services/gemini.py",
        "services/google_sheets.py",
        "services/whapi.py",
        "services/diagnostics.py",
        "services/gmail.py",
        "services/imap.py",
        "requirements.txt"
    ]
    
    output_file = "OLLAMA_CODE_DUMP.txt"
    
    with open(output_file, "w", encoding="utf-8") as out_f:
        out_f.write("# 🧠 OLLAMA PRE-TRAINING CONTEXT DUMP\n")
        out_f.write("Copy and paste this ENTIRE file into your local AI to give it full context of the Twin.\n\n")
        
        for file_path in target_files:
            if not os.path.exists(file_path):
                print(f"⚠️ Warning: {file_path} not found.")
                continue
                
            out_f.write(f"\n{'='*50}\n")
            out_f.write(f"FILE: {file_path}\n")
            out_f.write(f"{'='*50}\n\n")
            
            with open(file_path, "r", encoding="utf-8") as in_f:
                out_f.write(in_f.read())
                
    print(f"✅ SUCCESS! All your BackPocket Twin code has been combined into {output_file}.")
    print(f"📁 Size: {os.path.getsize(output_file) / 1024:.2f} KB")

if __name__ == "__main__":
    generate_ollama_dump()
