from fastapi import APIRouter, HTTPException, Query, Request
from models import GifListResponse, GifSummary, GifDetail
from database import get_conn

router = APIRouter()

def row_to_summary(row, storage_dir: str) -> GifSummary:
    return GifSummary(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        tags=[t.strip() for t in row["tags"].split(",") if t.strip()],
        gif_url=f"/static/gifs/{row['id']}.gif",
        created_at=row["created_at"],
        category=row["category"],
    )

@router.get("/api/gifs", response_model=GifListResponse)
async def list_gifs(request: Request, q: str = "", category: str = Query(default=""), limit: int = 100, offset: int = 0):
    limit = min(limit, 100)
    settings = request.app.state.settings
    conn = get_conn(settings.db_path)
    try:
        if q:
            pattern = f"%{q}%"
            cat_clause = " AND category=?" if category else ""
            cat_param = (category,) if category else ()
            rows = conn.execute(
                f"""SELECT * FROM gifs
                    WHERE status='approved'
                    AND (title LIKE ? OR description LIKE ? OR tags LIKE ?)
                    {cat_clause}
                    ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                (pattern, pattern, pattern, *cat_param, limit, offset)
            ).fetchall()
            total = conn.execute(
                f"""SELECT COUNT(*) FROM gifs
                    WHERE status='approved'
                    AND (title LIKE ? OR description LIKE ? OR tags LIKE ?)
                    {cat_clause}""",
                (pattern, pattern, pattern, *cat_param)
            ).fetchone()[0]
        else:
            cat_clause = " AND category=?" if category else ""
            cat_param = (category,) if category else ()
            rows = conn.execute(
                f"SELECT * FROM gifs WHERE status='approved'{cat_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (*cat_param, limit, offset)
            ).fetchall()
            total = conn.execute(
                f"SELECT COUNT(*) FROM gifs WHERE status='approved'{cat_clause}",
                cat_param
            ).fetchone()[0]
    finally:
        conn.close()

    return GifListResponse(
        results=[row_to_summary(r, settings.storage_dir) for r in rows],
        total=total,
        offset=offset,
    )

@router.get("/api/gifs/{gif_id}", response_model=GifDetail)
async def get_gif(gif_id: str, request: Request):
    settings = request.app.state.settings
    conn = get_conn(settings.db_path)
    try:
        row = conn.execute(
            "SELECT * FROM gifs WHERE id=? AND status='approved'", (gif_id,)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        raise HTTPException(404, detail="GIF not found")

    return GifDetail(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        tags=[t.strip() for t in row["tags"].split(",") if t.strip()],
        gif_url=f"/static/gifs/{row['id']}.gif",
        created_at=row["created_at"],
        submitter_name=row["submitter_name"],
        source_url=row["source_url"],
        source_start=row["source_start"],
        source_end=row["source_end"],
        category=row["category"],
    )
