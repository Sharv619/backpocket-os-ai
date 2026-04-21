import requests
from dotenv import load_dotenv

load_dotenv()

WHAPI_TOKEN = "b2Qy1r4VrMXzbuiOxR6WY2VXfEdlg0xn"

headers = {
    "accept": "application/json",
    "authorization": f"Bearer {WHAPI_TOKEN}"
}

url = "https://gate.whapi.cloud/health"
try:
    response = requests.get(url, headers=headers)
    print(f"Health Response: {response.text}")
    
    url_channel = "https://gate.whapi.cloud/settings"
    response_channel = requests.get(url_channel, headers=headers)
    print(f"Settings Response: {response_channel.text}")
except Exception as e:
    print(f"Error: {e}")
