import uuid
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from models import SubmitRequest
from jobs import job_store
from storage import move_file
from database import get_conn

router = APIRouter()

@router.post("/api/submit", status_code=201)
async def submit_gif(req: SubmitRequest, request: Request):
    job = job_store.get(req.job_id)
    if job is None:
        raise HTTPException(404, detail="Job not found or expired")
    if job["status"] != "done":
        raise HTTPException(400, detail="GIF generation not complete")

    if not job_store.mark_submitted(req.job_id):
        raise HTTPException(409, detail="This GIF has already been submitted")

    temp_path = Path(job["file_path"])
    if not temp_path.exists():
        raise HTTPException(410, detail="This GIF has expired — generate it again to submit")

    settings = request.app.state.settings
    gif_id = str(uuid.uuid4())
    dst = Path(settings.storage_dir) / "pending" / f"{gif_id}.gif"
    move_file(temp_path, dst)

    tags_str = ",".join(req.tags)
    now = datetime.now(timezone.utc).isoformat()
    conn = get_conn(settings.db_path)
    try:
        conn.execute(
            """INSERT INTO gifs
               (id, title, description, tags, submitter_name, submitter_email,
                file_path, status, created_at, source_url, source_start, source_end)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                gif_id, req.title, req.description, tags_str,
                req.submitter_name, req.submitter_email,
                str(dst), "pending", now,
                job["source_url"], job["source_start"], job["source_end"],
            )
        )
        conn.commit()
    finally:
        conn.close()

    return {"gif_id": gif_id, "message": "Submitted for review"}
