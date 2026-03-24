# backend/tests/test_config.py
import pytest
import os

def test_load_settings_raises_if_missing_hash(monkeypatch):
    monkeypatch.delenv("ADMIN_PASSWORD_HASH", raising=False)
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    from config import load_settings
    with pytest.raises(Exception):
        load_settings()

def test_load_settings_raises_if_secret_too_short(monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", "somehash")
    monkeypatch.setenv("SESSION_SECRET", "short")
    from config import load_settings
    with pytest.raises(ValueError, match="SESSION_SECRET must be at least 32 characters"):
        load_settings()

def test_load_settings_succeeds_with_valid_env(monkeypatch):
    monkeypatch.delenv("DB_PATH", raising=False)
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", "$2b$12$somebcrypthash")
    monkeypatch.setenv("SESSION_SECRET", "a" * 32)
    from config import load_settings
    s = load_settings()
    assert s.admin_password_hash == "$2b$12$somebcrypthash"
    assert s.db_path == "gifraffe.db"  # default
