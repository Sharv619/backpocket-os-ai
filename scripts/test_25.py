import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

def check():
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    print("Testing gemini-2.5-flash...")
    try:
        res = client.models.generate_content(model="gemini-2.5-flash", contents="Hi")
        print(f"✅ Success: {res.text[:50]}...")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    check()
