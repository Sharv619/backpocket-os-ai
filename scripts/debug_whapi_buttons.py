import requests
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('WHAPI_TOKEN')
phone = os.getenv('FOUNDER_PHONE')
clean_phone = "".join(filter(str.isdigit, phone))

url = "https://gate.whapi.cloud/messages/button"
headers = {
    "accept": "application/json",
    "authorization": f"Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "to": f"{clean_phone}@s.whatsapp.net",
    "body": "Hello! Testing Buttons.",
    "reply_buttons": [
        {"id": "btn001", "text": "Approve"},
        {"id": "btn002", "text": "Revise"}
    ]
}

response = requests.post(url, json=payload, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
