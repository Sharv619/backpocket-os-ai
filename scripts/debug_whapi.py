import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('WHAPI_TOKEN')
url = 'https://gate.whapi.cloud/settings'
headers = {'authorization': f'Bearer {token}'}

try:
    response = requests.get(url, headers=headers)
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
