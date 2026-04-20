import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

def list_models():
    # Use GEMINI_API_KEY explicitly
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        return

    print(f"Using GEMINI_API_KEY: {api_key[:10]}...")
    client = genai.Client(api_key=api_key)
    print("🚀 Listing available Gemini models:")
    
    # Try different model names
    models_to_try = [
        "gemini-1.5-flash",
        "gemini-2.0-flash-exp",
        "gemini-2.0-flash",
        "gemini-pro"
    ]
    
    for m in models_to_try:
        try:
            res = client.models.generate_content(model=m, contents="Hi")
            print(f"✅ {m} works! Response: {res.text[:50]}...")
        except Exception as e:
            print(f"❌ {m} failed: {e}")

if __name__ == "__main__":
    list_models()
