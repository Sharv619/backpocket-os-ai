import requests

try:
    response = requests.get('http://127.0.0.1:4040/api/tunnels')
    if response.status_code == 200:
        data = response.json()
        for tunnel in data['tunnels']:
            print(f"Name: {tunnel['name']}, Public URL: {tunnel['public_url']}, Proto: {tunnel['proto']}")
    else:
        print(f"Error: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
