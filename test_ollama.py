import base64
import requests

# Read and encode the image
with open("uploads/8cc8975c-101f-4c47-b790-2d62ae981da7.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

# Prepare the payload
payload = {
    "model": "moondream",
    "messages": [
        {
            "role": "user",
            "content": "What do you see in this image?",
            "images": [image_data],
        }
    ],
    "stream": False,
}

# Send request to Ollama
response = requests.post("http://localhost:11434/api/chat", json=payload)
print(response.text)
