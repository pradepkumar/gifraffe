import pytest
from datetime import datetime, timezone

def test_create_job_returns_id():
    from jobs import JobStore
    store = JobStore()
    job_id = store.create("https://youtube.com/watch?v=abc", 0.0, 5.0)
    assert len(job_id) == 36  # UUID format

def test_get_job_returns_job():
    from jobs import JobStore
    store = JobStore()
    job_id = store.create("https://youtube.com/watch?v=abc", 0.0, 5.0)
    job = store.get(job_id)
    assert job is not None
    assert job["status"] == "pending"
    assert job["source_url"] == "https://youtube.com/watch?v=abc"
    assert job["source_start"] == 0.0
    assert job["source_end"] == 5.0

def test_get_nonexistent_job_returns_none():
    from jobs import JobStore
    store = JobStore()
    assert store.get("nonexistent-id") is None

def test_update_job_step():
    from jobs import JobStore
    store = JobStore()
    job_id = store.create("https://youtube.com/watch?v=abc", 0.0, 5.0)
    store.set_step(job_id, "Downloading")
    job = store.get(job_id)
    assert job["step"] == "Downloading"
    assert job["status"] == "processing"

def test_complete_job():
    from jobs import JobStore
    store = JobStore()
    job_id = store.create("https://youtube.com/watch?v=abc", 0.0, 5.0)
    store.complete(job_id, "storage/temp/abc.gif")
    job = store.get(job_id)
    assert job["status"] == "done"
    assert job["file_path"] == "storage/temp/abc.gif"

def test_fail_job():
    from jobs import JobStore
    store = JobStore()
    job_id = store.create("https://youtube.com/watch?v=abc", 0.0, 5.0)
    store.fail(job_id, "Video unavailable")
    job = store.get(job_id)
    assert job["status"] == "failed"
    assert job["error"] == "Video unavailable"

def test_mark_submitted_prevents_double_submit():
    from jobs import JobStore
    store = JobStore()
    job_id = store.create("https://youtube.com/watch?v=abc", 0.0, 5.0)
    store.complete(job_id, "storage/temp/abc.gif")
    assert store.mark_submitted(job_id) is True
    assert store.mark_submitted(job_id) is False  # already submitted
