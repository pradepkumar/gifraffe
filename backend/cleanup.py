import asyncio
from pathlib import Path
from datetime import datetime, timezone

from jobs import job_store
from database import get_conn

TEMP_MAX_AGE_SECONDS = 3600      # 1 hour
PENDING_MAX_AGE_DAYS = 30

async def cleanup_loop(settings):
    while True:
        await asyncio.sleep(3600)  # run hourly
        _run_cleanup(settings)

def _run_cleanup(settings):
    storage_dir = settings.storage_dir
    db_path = settings.db_path

    # Purge old temp files
    temp_dir = Path(storage_dir) / "temp"
    if temp_dir.exists():
        now = datetime.now(timezone.utc).timestamp()
        for f in temp_dir.iterdir():
            if f.is_file() and (now - f.stat().st_mtime) > TEMP_MAX_AGE_SECONDS:
                f.unlink()
    job_store.purge_old(TEMP_MAX_AGE_SECONDS)

    # Purge old pending gifs
    conn = get_conn(db_path)
    try:
        cutoff = datetime.now(timezone.utc)
        rows = conn.execute(
            "SELECT id, file_path, created_at FROM gifs WHERE status='pending'"
        ).fetchall()
        to_delete = []
        for row in rows:
            try:
                created = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
                age_days = (cutoff - created).days
                if age_days >= PENDING_MAX_AGE_DAYS:
                    to_delete.append(row)
            except (ValueError, KeyError):
                pass
        for row in to_delete:
            Path(row["file_path"]).unlink(missing_ok=True)
            conn.execute("DELETE FROM gifs WHERE id=?", (row["id"],))
        conn.commit()
    finally:
        conn.close()

def start_cleanup_task(settings):
    _run_cleanup(settings)  # run once on startup
    return asyncio.ensure_future(cleanup_loop(settings))
