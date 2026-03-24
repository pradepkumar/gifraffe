import os
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Settings:
    admin_password_hash: str
    session_secret: str
    db_path: str
    storage_dir: str

def load_settings() -> Settings:
    admin_hash = os.environ.get("ADMIN_PASSWORD_HASH", "").strip()
    session_secret = os.environ.get("SESSION_SECRET", "").strip()

    if not admin_hash:
        raise RuntimeError("Missing required env var: ADMIN_PASSWORD_HASH")
    if not session_secret:
        raise RuntimeError("Missing required env var: SESSION_SECRET")
    if len(session_secret) < 32:
        raise ValueError("SESSION_SECRET must be at least 32 characters")

    return Settings(
        admin_password_hash=admin_hash,
        session_secret=session_secret,
        db_path=os.environ.get("DB_PATH", str(Path(__file__).parent / "gifraffe.db")),
        storage_dir=os.environ.get("STORAGE_DIR", str(Path(__file__).parent / "storage")),
    )
