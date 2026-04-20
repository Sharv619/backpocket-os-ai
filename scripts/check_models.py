import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

def list_models():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        return

    client = genai.Client(api_key=api_key)
    print("🚀 Listing available Gemini models:")
    try:
        # The new SDK might have a different way to list models
        # but let's try to just generate something with a known model to verify
        res = client.models.generate_content(model="gemini-1.5-flash", contents="Hi")
        print(f"✅ gemini-1.5-flash works! Response: {res.text}")
    except Exception as e:
        print(f"❌ gemini-1.5-flash failed: {e}")
        
    try:
        res = client.models.generate_content(model="gemini-2.0-flash-exp", contents="Hi")
        print(f"✅ gemini-2.0-flash-exp works! Response: {res.text}")
    except Exception as e:
        print(f"❌ gemini-2.0-flash-exp failed: {e}")

    try:
        res = client.models.generate_content(model="gemini-2.0-flash", contents="Hi")
        print(f"✅ gemini-2.0-flash works! Response: {res.text}")
    except Exception as e:
        print(f"❌ gemini-2.0-flash failed: {e}")

if __name__ == "__main__":
    list_models()
