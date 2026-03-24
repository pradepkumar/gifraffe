import sqlite3
from pathlib import Path

CREATE_GIFS_TABLE = """
CREATE TABLE IF NOT EXISTS gifs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    tags TEXT NOT NULL,
    submitter_name TEXT NOT NULL,
    submitter_email TEXT,
    file_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_start REAL NOT NULL,
    source_end REAL NOT NULL
)
"""

def init_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(CREATE_GIFS_TABLE)
    conn.commit()
    conn.close()

def get_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
