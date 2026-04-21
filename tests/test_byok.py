"""Tests for SOVEREIGN ENGINE — BYOK service."""

import pytest


@pytest.fixture(autouse=True)
def set_encryption_key(monkeypatch, tmp_path):
    from cryptography.fernet import Fernet
    monkeypatch.setenv("BP_ENCRYPTION_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("BP_DB_PATH", str(tmp_path / "test.db"))
    # Patch DB_PATH in byok module before import
    import services.database as db_mod
    monkeypatch.setattr(db_mod, "DB_PATH", str(tmp_path / "test.db"))
    db_mod.init_db()


def _get_byok():
    import importlib
    import services.byok as byok_mod
    importlib.reload(byok_mod)
    return byok_mod


def test_save_and_retrieve_key(tmp_path, monkeypatch):
    import services.database as db_mod
    monkeypatch.setattr(db_mod, "DB_PATH", str(tmp_path / "test.db"))
    db_mod.init_db()

    import services.byok as byok
    import importlib
    importlib.reload(byok)

    byok.save_byok_key("user123", "openrouter", "sk-or-test-key")
    key = byok.get_effective_key("user123", "openrouter")
    assert key == "sk-or-test-key"


def test_status_shows_configured(tmp_path, monkeypatch):
    import services.database as db_mod
    monkeypatch.setattr(db_mod, "DB_PATH", str(tmp_path / "test.db"))
    db_mod.init_db()

    import services.byok as byok
    import importlib
    importlib.reload(byok)

    byok.save_byok_key("user456", "gemini", "AIza-test")
    status = byok.get_byok_status("user456")
    assert status["gemini"]["configured"] is True
    assert status["openrouter"]["configured"] is False
    assert status["elevenlabs"]["configured"] is False


def test_delete_key(tmp_path, monkeypatch):
    import services.database as db_mod
    monkeypatch.setattr(db_mod, "DB_PATH", str(tmp_path / "test.db"))
    db_mod.init_db()

    import services.byok as byok
    import importlib
    importlib.reload(byok)

    byok.save_byok_key("user789", "elevenlabs", "el-test-key")
    byok.delete_byok_key("user789", "elevenlabs")
    key = byok.get_effective_key("user789", "elevenlabs")
    assert key == ""


def test_no_user_returns_empty():
    import services.byok as byok
    assert byok.get_effective_key("", "openrouter") == ""


def test_unknown_user_returns_empty(tmp_path, monkeypatch):
    import services.database as db_mod
    monkeypatch.setattr(db_mod, "DB_PATH", str(tmp_path / "test.db"))
    db_mod.init_db()

    import services.byok as byok
    import importlib
    importlib.reload(byok)

    key = byok.get_effective_key("nonexistent-user", "openrouter")
    assert key == ""


def test_supported_providers():
    import services.byok as byok
    assert set(byok.SUPPORTED_PROVIDERS) == {"openrouter", "gemini", "elevenlabs"}
