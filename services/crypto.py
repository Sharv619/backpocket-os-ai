"""Symmetric encryption for secrets at rest using Fernet (AES-128-CBC + HMAC-SHA256)."""
import os
import json
from cryptography.fernet import Fernet

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        key = os.environ.get("BP_ENCRYPTION_KEY")
        if not key:
            raise RuntimeError(
                "BP_ENCRYPTION_KEY not set. "
                "Generate one: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def encrypt_dict(data: dict) -> str:
    """JSON-encode dict, encrypt, return URL-safe base64 string."""
    plaintext = json.dumps(data).encode()
    return _get_fernet().encrypt(plaintext).decode()


def decrypt_dict(token: str) -> dict:
    """Decrypt URL-safe base64 string, return dict."""
    plaintext = _get_fernet().decrypt(token.encode() if isinstance(token, str) else token)
    return json.loads(plaintext)


def encrypt_str(value: str) -> str:
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt_str(token: str) -> str:
    return _get_fernet().decrypt(token.encode() if isinstance(token, str) else token).decode()


def is_encrypted(value: str) -> bool:
    """Heuristic: Fernet tokens start with 'gAAAAA'."""
    return isinstance(value, str) and value.startswith("gAAAAA")


def generate_key() -> str:
    """Print a new key suitable for BP_ENCRYPTION_KEY."""
    return Fernet.generate_key().decode()
