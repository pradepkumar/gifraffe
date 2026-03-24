import pytest
from unittest.mock import patch
from pathlib import Path

@pytest.fixture
def done_job(client, tmp_path):
    """Create a job in 'done' state with a real temp file."""
    from jobs import job_store
    import os
    storage_dir = os.environ["STORAGE_DIR"]
    Path(storage_dir, "temp").mkdir(parents=True, exist_ok=True)

    with patch("routes.generate.run_generate_job"):
        resp = client.post("/api/generate", json={
            "url": "https://www.youtube.com/watch?v=abc", "start": 0, "end": 5
        })
    job_id = resp.json()["job_id"]
    gif_path = Path(storage_dir, "temp", f"{job_id}.gif")
    gif_path.write_bytes(b"GIF89a")  # fake GIF file
    job_store.complete(job_id, str(gif_path))
    return job_id

def test_submit_returns_gif_id(client, done_job):
    resp = client.post("/api/submit", json={
        "job_id": done_job,
        "title": "Funny scene",
        "tags": ["funny", "comedy"],
        "submitter_name": "Ravi",
    })
    assert resp.status_code == 201
    assert "gif_id" in resp.json()

def test_submit_moves_file_to_pending(client, done_job):
    import os
    storage_dir = os.environ["STORAGE_DIR"]
    client.post("/api/submit", json={
        "job_id": done_job,
        "title": "Funny scene",
        "tags": ["funny", "comedy"],
        "submitter_name": "Ravi",
    })
    pending_files = list(Path(storage_dir, "pending").iterdir())
    assert len(pending_files) == 1

def test_submit_returns_409_on_double_submit(client, done_job):
    payload = {"job_id": done_job, "title": "T", "tags": ["t"], "submitter_name": "R"}
    client.post("/api/submit", json=payload)
    resp = client.post("/api/submit", json=payload)
    assert resp.status_code == 409

def test_submit_returns_404_for_unknown_job(client):
    resp = client.post("/api/submit", json={
        "job_id": "unknown", "title": "T", "tags": ["t"], "submitter_name": "R"
    })
    assert resp.status_code == 404

def test_submit_returns_400_if_job_not_done(client):
    from jobs import job_store
    job_id = job_store.create("https://youtube.com/watch?v=abc", 0, 5)
    resp = client.post("/api/submit", json={
        "job_id": job_id, "title": "T", "tags": ["t"], "submitter_name": "R"
    })
    assert resp.status_code == 400
