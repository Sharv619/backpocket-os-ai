#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv
load_dotenv(override=True)

api_key = os.getenv("OPENROUTER_API_KEY")
print(f"API Key loaded: {api_key[:20]}..." if api_key else "No API key found")
print(f"API Key length: {len(api_key) if api_key else 0}")

# Test simple API call
import requests
try:
    print("\n📡 Testing OpenRouter API connection...")
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "backpocket.ai",
        },
        json={
            "model": "mistralai/mistral-7b-instruct:free",
            "messages": [{"role": "user", "content": "Say hello in one word"}],
            "temperature": 0.7,
            "max_tokens": 50,
        },
        timeout=10,
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"✓ OpenRouter is working!")
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        print(f"Response: {content}")
    else:
        print(f"✗ Error: {response.status_code}")
        print(f"Details: {response.text[:300]}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
