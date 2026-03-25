import pytest
import os
import bcrypt

TEST_PASSWORD = "testpassword123"

@pytest.fixture(scope="session")
def test_password_hash():
    return bcrypt.hashpw(TEST_PASSWORD.encode(), bcrypt.gensalt()).decode()

@pytest.fixture(autouse=True)
def set_test_env(monkeypatch, tmp_path, test_password_hash):
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", test_password_hash)
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret-minimum-32chars!")
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))
    # Reset the rate limiter for each test
    import sys
    if "rate_limiter" in sys.modules:
        from rate_limiter import rate_limiter
        rate_limiter._requests.clear()

@pytest.fixture
def client(set_test_env):
    """Fresh TestClient per test — reimports app with current env vars."""
    import importlib
    import sys
    # Remove cached modules so they reload with fresh env
    for mod in list(sys.modules.keys()):
        if mod.startswith(("main", "config", "database", "storage", "jobs",
                            "routes", "cleanup", "gif_generator", "models")):
            del sys.modules[mod]
    import main
    from fastapi.testclient import TestClient
    # Use context manager to ensure lifespan runs
    with TestClient(main.app, raise_server_exceptions=True) as tc:
        yield tc
