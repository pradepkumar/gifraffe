import pytest
from unittest.mock import patch, MagicMock

def test_generate_rejects_non_youtube_url(client):
    resp = client.post("/api/generate", json={"url": "https://vimeo.com/123", "start": 0, "end": 5})
    assert resp.status_code == 400
    assert "YouTube" in resp.json()["detail"]

def test_generate_rejects_duration_over_10s(client):
    resp = client.post("/api/generate", json={
        "url": "https://www.youtube.com/watch?v=abc", "start": 0, "end": 11
    })
    assert resp.status_code == 400
    assert "10 seconds" in resp.json()["detail"]

def test_generate_rejects_inverted_times(client):
    resp = client.post("/api/generate", json={
        "url": "https://www.youtube.com/watch?v=abc", "start": 10, "end": 5
    })
    assert resp.status_code == 400

def test_generate_returns_job_id(client):
    with patch("routes.generate.run_generate_job"):
        resp = client.post("/api/generate", json={
            "url": "https://www.youtube.com/watch?v=abc", "start": 0, "end": 5
        })
    assert resp.status_code == 202
    assert "job_id" in resp.json()

def test_get_job_returns_404_for_unknown(client):
    resp = client.get("/api/jobs/nonexistent-id")
    assert resp.status_code == 404

def test_get_job_returns_status(client):
    with patch("routes.generate.run_generate_job"):
        create_resp = client.post("/api/generate", json={
            "url": "https://www.youtube.com/watch?v=abc", "start": 0, "end": 5
        })
    job_id = create_resp.json()["job_id"]
    resp = client.get(f"/api/jobs/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] in ("pending", "processing", "done", "failed")
