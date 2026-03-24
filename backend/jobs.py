import uuid
from datetime import datetime, timezone
from threading import Lock

class JobStore:
    def __init__(self):
        self._jobs: dict = {}
        self._lock = Lock()

    def create(self, source_url: str, source_start: float, source_end: float) -> str:
        job_id = str(uuid.uuid4())
        with self._lock:
            self._jobs[job_id] = {
                "id": job_id,
                "status": "pending",
                "step": None,
                "file_path": None,
                "error": None,
                "source_url": source_url,
                "source_start": source_start,
                "source_end": source_end,
                "submitted": False,
                "created_at": datetime.now(timezone.utc),
            }
        return job_id

    def get(self, job_id: str) -> dict | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None

    def set_step(self, job_id: str, step: str) -> None:
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["step"] = step
                self._jobs[job_id]["status"] = "processing"

    def complete(self, job_id: str, file_path: str) -> None:
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = "done"
                self._jobs[job_id]["step"] = "Done"
                self._jobs[job_id]["file_path"] = file_path

    def fail(self, job_id: str, error: str) -> None:
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = "failed"
                self._jobs[job_id]["error"] = error

    def mark_submitted(self, job_id: str) -> bool:
        """Returns True if successfully marked, False if already submitted."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or job["submitted"]:
                return False
            job["submitted"] = True
            return True

    def purge_old(self, max_age_seconds: float) -> None:
        """Remove jobs older than max_age_seconds."""
        now = datetime.now(timezone.utc)
        with self._lock:
            to_delete = [
                jid for jid, j in self._jobs.items()
                if (now - j["created_at"]).total_seconds() > max_age_seconds
            ]
            for jid in to_delete:
                del self._jobs[jid]

# Global instance — shared across requests
job_store = JobStore()
