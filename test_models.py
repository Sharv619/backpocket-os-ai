#!/usr/bin/env python3
import requests
import os
from dotenv import load_dotenv

load_dotenv(override=True)
api_key = os.getenv("OPENROUTER_API_KEY")

# Test with known working free models
test_models = [
    "nousresearch/nous-hermes-2-mixtral-8x7b-dpo:free",
    "meta-llama/llama-2-7b-chat:free",
    "mistralai/mistral-7b-instruct",
    "openrouter/auto",
]

for model in test_models:
    print(f"\n🔄 Testing model: {model}")
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "backpocket.ai",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Say hi in one word"}],
                "temperature": 0.7,
                "max_tokens": 50,
            },
            timeout=10,
        )
        if response.status_code == 200:
            print(f"✓ {model} works!")
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"  Response: {content}")
            print(f"\n✅ Found working model: {model}")
            break
        else:
            error_info = response.json() if response.status_code < 500 else response.text
            print(f"✗ {model} - Status {response.status_code}")
            if isinstance(error_info, dict) and 'error' in error_info:
                print(f"  Error: {error_info['error'].get('message', 'Unknown error')}")
    except Exception as e:
        print(f"✗ {model} - Error: {type(e).__name__}: {e}")
