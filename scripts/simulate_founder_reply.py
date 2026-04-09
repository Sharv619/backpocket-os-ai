import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
founder_phone = "".join(filter(str.isdigit, os.getenv("FOUNDER_PHONE", "+61424180030")))

def simulate_reply(text):
    url = "http://127.0.0.1:8000/webhook/whatsapp"
    payload = {
        "messages": [
            {
                "from_me": False,
                "text": {"body": text},
                "from": f"{founder_phone}@s.whatsapp.net"
            }
        ]
    }
    
    print(f"Simulating founder reply: '{text}'")
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    # Simulate the two commands the founder tried to send
    simulate_reply("approve 4253")
    simulate_reply("revise 2840 with my notes already")
