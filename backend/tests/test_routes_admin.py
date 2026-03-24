import pytest, os, uuid
from pathlib import Path
from database import get_conn
from datetime import datetime, timezone

TEST_PASSWORD = "testpassword123"

def insert_pending_gif(db_path: str, storage_dir: str) -> str:
    gid = str(uuid.uuid4())
    gif_file = Path(storage_dir) / "pending" / f"{gid}.gif"
    gif_file.parent.mkdir(parents=True, exist_ok=True)
    gif_file.write_bytes(b"GIF89a")
    conn = get_conn(db_path)
    conn.execute(
        """INSERT INTO gifs
           (id, title, description, tags, submitter_name, file_path, status,
            created_at, source_url, source_start, source_end)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (gid, "Test", None, "tag1", "Ravi", str(gif_file), "pending",
         datetime.now(timezone.utc).isoformat(),
         "https://youtube.com/watch?v=abc", 0.0, 5.0)
    )
    conn.commit()
    conn.close()
    return gid

def login(client):
    resp = client.post("/api/admin/login", json={"password": TEST_PASSWORD})
    assert resp.status_code == 200
    return resp.cookies

def test_login_succeeds_with_correct_password(client):
    resp = client.post("/api/admin/login", json={"password": TEST_PASSWORD})
    assert resp.status_code == 200

def test_login_fails_with_wrong_password(client):
    resp = client.post("/api/admin/login", json={"password": "wrong"})
    assert resp.status_code == 401

def test_queue_requires_auth(client):
    resp = client.get("/api/admin/queue")
    assert resp.status_code == 401

def test_queue_returns_pending_gifs(client):
    db_path = os.environ["DB_PATH"]
    storage_dir = os.environ["STORAGE_DIR"]
    insert_pending_gif(db_path, storage_dir)
    cookies = login(client)
    resp = client.get("/api/admin/queue", cookies=cookies)
    assert resp.status_code == 200
    assert len(resp.json()["results"]) == 1

def test_approve_moves_to_approved(client):
    db_path = os.environ["DB_PATH"]
    storage_dir = os.environ["STORAGE_DIR"]
    gid = insert_pending_gif(db_path, storage_dir)
    cookies = login(client)
    resp = client.post(f"/api/admin/approve/{gid}", cookies=cookies)
    assert resp.status_code == 200
    conn = get_conn(db_path)
    row = conn.execute("SELECT status FROM gifs WHERE id=?", (gid,)).fetchone()
    conn.close()
    assert row["status"] == "approved"
    assert Path(storage_dir, "gifs", f"{gid}.gif").exists()

def test_reject_deletes_gif(client):
    db_path = os.environ["DB_PATH"]
    storage_dir = os.environ["STORAGE_DIR"]
    gid = insert_pending_gif(db_path, storage_dir)
    cookies = login(client)
    resp = client.post(f"/api/admin/reject/{gid}", cookies=cookies)
    assert resp.status_code == 200
    conn = get_conn(db_path)
    row = conn.execute("SELECT * FROM gifs WHERE id=?", (gid,)).fetchone()
    conn.close()
    assert row is None
    assert not Path(storage_dir, "pending", f"{gid}.gif").exists()

def test_pending_gif_requires_auth(client):
    resp = client.get("/api/admin/pending/someid")
    assert resp.status_code == 401

def test_pending_gif_serves_file(client):
    db_path = os.environ["DB_PATH"]
    storage_dir = os.environ["STORAGE_DIR"]
    gid = insert_pending_gif(db_path, storage_dir)
    cookies = login(client)
    resp = client.get(f"/api/admin/pending/{gid}", cookies=cookies)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/gif"

def test_approve_updates_fields(client):
    db_path = os.environ["DB_PATH"]
    storage_dir = os.environ["STORAGE_DIR"]
    gid = insert_pending_gif(db_path, storage_dir)
    cookies = login(client)
    resp = client.post(
        f"/api/admin/approve/{gid}",
        json={"title": "Updated", "tags": ["new"], "description": "desc"},
        cookies=cookies,
    )
    assert resp.status_code == 200
    conn = get_conn(db_path)
    row = conn.execute("SELECT * FROM gifs WHERE id=?", (gid,)).fetchone()
    conn.close()
    assert row["title"] == "Updated"
    assert row["tags"] == "new"
    assert row["description"] == "desc"
    assert row["status"] == "approved"

def test_approve_empty_body_preserves_fields(client):
    db_path = os.environ["DB_PATH"]
    storage_dir = os.environ["STORAGE_DIR"]
    gid = insert_pending_gif(db_path, storage_dir)
    cookies = login(client)
    resp = client.post(f"/api/admin/approve/{gid}", json={}, cookies=cookies)
    assert resp.status_code == 200
    conn = get_conn(db_path)
    row = conn.execute("SELECT * FROM gifs WHERE id=?", (gid,)).fetchone()
    conn.close()
    assert row["title"] == "Test"
    assert row["tags"] == "tag1"
    assert row["description"] is None
    assert row["status"] == "approved"
