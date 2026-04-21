import requests
from dotenv import load_dotenv

load_dotenv()

WHAPI_TOKEN = "b2Qy1r4VrMXzbuiOxR6WY2VXfEdlg0xn"
# Using a dummy number just to see the response code
TO_NUMBER = "61424180030"

headers = {
    "accept": "application/json",
    "authorization": f"Bearer {WHAPI_TOKEN}"
}

url = "https://gate.whapi.cloud/messages/text"
payload = {
    "to": TO_NUMBER,
    "body": "Test from antigravity diagnostic script"
}

try:
    print(f"Testing Whapi with Token: {WHAPI_TOKEN[:5]}...")
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
