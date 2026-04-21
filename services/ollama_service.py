"""
AI Service Wrapper for local Ollama models.
"""
import os
import requests
import logging

logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.default_model = os.getenv("OLLAMA_MODEL", "gemma2:2b")
        self.vision_model = "moondream" # Common vision model for Ollama

    def analyze(self, prompt: str, model: str = None) -> str:
        """
        Sends a prompt to a local Ollama model for general analysis.
        """
        model = model or self.default_model
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            # The structure of Ollama's non-streaming response is different
            return response.json().get("response", "")
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama request failed: {e}")
            return f"Error: Could not connect to Ollama at {self.base_url}. Is it running? {e}"

    def analyze_vision(self, prompt: str, image_b64: str, model: str = None) -> str:
        """
        Sends a prompt and a base64 encoded image to an Ollama vision model.
        Note: The 'ollama' library handles this more gracefully, but we use 'requests' for consistency.
        """
        model = model or self.vision_model
        url = f"{self.base_url}/api/chat" # Vision models often use the chat endpoint

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image_b64]
                }
            ],
            "stream": False
        }

        try:
            response = requests.post(url, json=payload, timeout=90)
            response.raise_for_status()
            return response.json()["message"]["content"]
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama vision request failed: {e}")
            return f"Error: Could not connect to Ollama vision endpoint. {e}"
        except (KeyError, IndexError) as e:
            logger.error(f"Invalid vision response from Ollama: {response.text[:200]}")
            return f"Error: Invalid vision response from Ollama. {e}"

