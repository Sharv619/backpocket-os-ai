import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('WHAPI_TOKEN')
long_url = "https://backpocket-os.backpocketsystem.io/webhook/whatsapp"

settings_url = 'https://gate.whapi.cloud/settings'
headers = {
    'authorization': f'Bearer {token}',
    'content-type': 'application/json'
}

payload = {
    "webhooks": [
        {
            "url": long_url,
            "events": [
                {"type": "messages", "method": "post"}
            ],
            "mode": "body"
        }
    ]
}

print(f"Setting webhook to: {long_url}")
response = requests.patch(settings_url, headers=headers, json=payload)
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))
