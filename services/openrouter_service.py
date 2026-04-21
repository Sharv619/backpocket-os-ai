"""
AI Service Wrapper for OpenRouter and other cloud-based models.
"""
import os
import requests
import logging

logger = logging.getLogger(__name__)

class OpenRouterService:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY is not set. Cloud AI features will be disabled.")

    def analyze(self, prompt: str, model: str = None) -> str:
        """
        Sends a prompt to a powerful language model for general analysis.
        """
        if not self.api_key:
            return "Error: OpenRouter API key not configured."

        # Default to a strong model if none is provided
        model = model or os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://backpocket.os",
            "X-Title": "BackPocket OS",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
        }

        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=90)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter request failed: {e}")
            return f"Error: Could not connect to OpenRouter. {e}"
        except (KeyError, IndexError) as e:
            logger.error(f"Invalid response from OpenRouter: {response.text[:200]}")
            return f"Error: Invalid response from OpenRouter. {e}"

    def analyze_vision(self, prompt: str, image_b64: str, model: str = None) -> str:
        """
        Sends a prompt and a base64 encoded image to a vision model.
        """
        if not self.api_key:
            return "Error: OpenRouter API key not configured."
            
        model = model or os.getenv("OPENROUTER_VISION_MODEL", "google/gemini-2.5-flash-image")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://backpocket.os",
            "X-Title": "BackPocket OS",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                        },
                    ],
                }
            ],
            "max_tokens": 512,
        }

        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter vision request failed: {e}")
            return f"Error: Could not connect to OpenRouter vision API. {e}"
        except (KeyError, IndexError) as e:
            logger.error(f"Invalid vision response from OpenRouter: {response.text[:200]}")
            return f"Error: Invalid vision response from OpenRouter. {e}"
