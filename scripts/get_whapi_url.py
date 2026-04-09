import requests
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('WHAPI_TOKEN')
url = 'https://gate.whapi.cloud/settings'
headers = {'authorization': f'Bearer {token}'}

try:
    data = requests.get(url, headers=headers).json()
    print("CURRENT_WEBHOOK_URL:")
    print(data['webhooks'][0]['url'])
except Exception as e:
    print(f"Error: {e}")
