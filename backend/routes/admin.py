from pathlib import Path
from fastapi import APIRouter, Cookie, HTTPException, Request, Response
from fastapi.responses import FileResponse
import bcrypt
from itsdangerous import TimestampSigner, BadSignature, SignatureExpired
from models import AdminLoginRequest, AdminGifItem
from database import get_conn
from storage import move_file, delete_file

router = APIRouter()
SESSION_COOKIE = "gifraffe_session"
SESSION_MAX_AGE = 24 * 60 * 60  # 24 hours

def _signer(secret: str) -> TimestampSigner:
    return TimestampSigner(secret)

def _require_auth(request: Request, gifraffe_session: str | None = Cookie(default=None)):
    secret = request.app.state.settings.session_secret
    if not gifraffe_session:
        raise HTTPException(401, detail="Authentication required")
    try:
        _signer(secret).unsign(gifraffe_session, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        raise HTTPException(401, detail="Session expired or invalid")

@router.post("/api/admin/login")
async def admin_login(req: AdminLoginRequest, request: Request, response: Response):
    settings = request.app.state.settings
    if not bcrypt.checkpw(req.password.encode(), settings.admin_password_hash.encode()):
        raise HTTPException(401, detail="Invalid password")
    token = _signer(settings.session_secret).sign("admin").decode()
    response.set_cookie(
        SESSION_COOKIE, token,
        httponly=True, samesite="strict", max_age=SESSION_MAX_AGE
    )
    return {"ok": True}

@router.get("/api/admin/queue")
async def get_queue(
    request: Request,
    gifraffe_session: str | None = Cookie(default=None),
):
    _require_auth(request, gifraffe_session)
    settings = request.app.state.settings
    conn = get_conn(settings.db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM gifs WHERE status='pending' ORDER BY created_at ASC"
        ).fetchall()
    finally:
        conn.close()

    results = [
        AdminGifItem(
            id=r["id"], title=r["title"], description=r["description"],
            tags=[t.strip() for t in r["tags"].split(",") if t.strip()],
            submitter_name=r["submitter_name"], submitter_email=r["submitter_email"],
            gif_url=f"/api/admin/pending/{r['id']}",
            source_url=r["source_url"], source_start=r["source_start"],
            source_end=r["source_end"], created_at=r["created_at"],
        )
        for r in rows
    ]
    return {"results": results}

@router.get("/api/admin/pending/{gif_id}")
async def serve_pending_gif(
    gif_id: str,
    request: Request,
    gifraffe_session: str | None = Cookie(default=None),
):
    _require_auth(request, gifraffe_session)
    settings = request.app.state.settings
    path = Path(settings.storage_dir) / "pending" / f"{gif_id}.gif"
    if not path.exists():
        raise HTTPException(404, detail="File not found")
    return FileResponse(str(path), media_type="image/gif")

@router.post("/api/admin/approve/{gif_id}")
async def approve_gif(
    gif_id: str,
    request: Request,
    gifraffe_session: str | None = Cookie(default=None),
):
    _require_auth(request, gifraffe_session)
    settings = request.app.state.settings
    conn = get_conn(settings.db_path)
    try:
        row = conn.execute("SELECT * FROM gifs WHERE id=? AND status='pending'", (gif_id,)).fetchone()
        if not row:
            raise HTTPException(404, detail="Pending GIF not found")
        src = Path(settings.storage_dir) / "pending" / f"{gif_id}.gif"
        dst = Path(settings.storage_dir) / "gifs" / f"{gif_id}.gif"
        move_file(src, dst)
        conn.execute("UPDATE gifs SET status='approved', file_path=? WHERE id=?", (str(dst), gif_id))
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}

@router.post("/api/admin/reject/{gif_id}")
async def reject_gif(
    gif_id: str,
    request: Request,
    gifraffe_session: str | None = Cookie(default=None),
):
    _require_auth(request, gifraffe_session)
    settings = request.app.state.settings
    conn = get_conn(settings.db_path)
    try:
        row = conn.execute("SELECT * FROM gifs WHERE id=? AND status='pending'", (gif_id,)).fetchone()
        if not row:
            raise HTTPException(404, detail="Pending GIF not found")
        delete_file(Path(settings.storage_dir) / "pending" / f"{gif_id}.gif")
        conn.execute("DELETE FROM gifs WHERE id=?", (gif_id,))
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}
