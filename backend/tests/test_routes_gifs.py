import pytest
from database import get_conn, init_db
from datetime import datetime, timezone
import os, uuid

def insert_gif(db_path, status="approved", title="Test GIF", tags="funny,test"):
    gid = str(uuid.uuid4())
    conn = get_conn(db_path)
    conn.execute(
        """INSERT INTO gifs
           (id, title, description, tags, submitter_name, file_path, status,
            created_at, source_url, source_start, source_end)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (gid, title, "desc", tags, "Ravi",
         f"storage/gifs/{gid}.gif", status,
         datetime.now(timezone.utc).isoformat(),
         "https://youtube.com/watch?v=abc", 0.0, 5.0)
    )
    conn.commit()
    conn.close()
    return gid

def test_list_gifs_empty(client):
    resp = client.get("/api/gifs")
    assert resp.status_code == 200
    assert resp.json()["results"] == []
    assert resp.json()["total"] == 0

def test_list_gifs_returns_approved_only(client):
    db_path = os.environ["DB_PATH"]
    approved_id = insert_gif(db_path, status="approved")
    insert_gif(db_path, status="pending")
    resp = client.get("/api/gifs")
    assert resp.status_code == 200
    ids = [g["id"] for g in resp.json()["results"]]
    assert approved_id in ids
    assert len(ids) == 1

def test_search_by_title(client):
    db_path = os.environ["DB_PATH"]
    insert_gif(db_path, title="Vijay entry scene", tags="vijay")
    insert_gif(db_path, title="Ajith comedy", tags="ajith")
    resp = client.get("/api/gifs?q=vijay")
    assert len(resp.json()["results"]) == 1
    assert "Vijay" in resp.json()["results"][0]["title"]

def test_search_by_tag(client):
    db_path = os.environ["DB_PATH"]
    insert_gif(db_path, title="Some GIF", tags="vijay,comedy")
    insert_gif(db_path, title="Other GIF", tags="ajith,action")
    resp = client.get("/api/gifs?q=comedy")
    assert len(resp.json()["results"]) == 1

def test_get_gif_detail(client):
    db_path = os.environ["DB_PATH"]
    gid = insert_gif(db_path)
    resp = client.get(f"/api/gifs/{gid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == gid

def test_get_gif_returns_404_for_pending(client):
    db_path = os.environ["DB_PATH"]
    gid = insert_gif(db_path, status="pending")
    resp = client.get(f"/api/gifs/{gid}")
    assert resp.status_code == 404

def test_tags_returned_as_list(client):
    db_path = os.environ["DB_PATH"]
    insert_gif(db_path, tags="vijay,comedy,entry")
    resp = client.get("/api/gifs")
    assert resp.json()["results"][0]["tags"] == ["vijay", "comedy", "entry"]
