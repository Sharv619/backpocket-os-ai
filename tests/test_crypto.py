"""Tests for Fernet encryption service."""
import os
import pytest
from cryptography.fernet import Fernet


@pytest.fixture(autouse=True)
def set_encryption_key(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("BP_ENCRYPTION_KEY", key)
    # Reset cached _fernet so fresh key is used each test
    import services.crypto as crypto_mod
    crypto_mod._fernet = None
    yield
    crypto_mod._fernet = None


class TestEncryptDecrypt:
    def test_encrypt_decrypt_string_roundtrip(self):
        from services.crypto import encrypt_str, decrypt_str
        original = "secret_oauth_token_12345"
        encrypted = encrypt_str(original)
        assert encrypted != original
        assert decrypt_str(encrypted) == original

    def test_encrypt_decrypt_dict_roundtrip(self):
        from services.crypto import encrypt_dict, decrypt_dict
        data = {"access_token": "ya29.abc", "refresh_token": "1//xyz", "client_id": "foo"}
        encrypted = encrypt_dict(data)
        assert isinstance(encrypted, str)
        result = decrypt_dict(encrypted)
        assert result == data

    def test_encrypted_starts_with_gaaaaa(self):
        from services.crypto import encrypt_str
        enc = encrypt_str("test")
        assert enc.startswith("gAAAAA")

    def test_is_encrypted_detects_token(self):
        from services.crypto import encrypt_str, is_encrypted
        enc = encrypt_str("test")
        assert is_encrypted(enc)
        assert not is_encrypted("plaintext_string")
        assert not is_encrypted("")

    def test_different_plaintexts_produce_different_ciphertexts(self):
        from services.crypto import encrypt_str
        assert encrypt_str("abc") != encrypt_str("xyz")

    def test_wrong_key_raises(self):
        from services.crypto import encrypt_str
        import services.crypto as crypto_mod
        encrypted = encrypt_str("secret")
        # Swap to a different key
        crypto_mod._fernet = None
        os.environ["BP_ENCRYPTION_KEY"] = Fernet.generate_key().decode()
        crypto_mod._fernet = None
        from services.crypto import decrypt_str
        with pytest.raises(Exception):  # InvalidToken or similar
            decrypt_str(encrypted)

    def test_generate_key_returns_valid_fernet_key(self):
        from services.crypto import generate_key
        key = generate_key()
        assert isinstance(key, str)
        f = Fernet(key.encode())  # should not raise
        assert f is not None


class TestNoKeySet:
    def test_raises_without_key(self, monkeypatch):
        import services.crypto as crypto_mod
        monkeypatch.delenv("BP_ENCRYPTION_KEY", raising=False)
        crypto_mod._fernet = None
        from services.crypto import encrypt_str
        with pytest.raises(RuntimeError, match="BP_ENCRYPTION_KEY"):
            encrypt_str("test")
        crypto_mod._fernet = None
