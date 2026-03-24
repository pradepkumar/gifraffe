from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from models import GenerateRequest, JobResponse
from jobs import job_store
from gif_generator import is_youtube_url, validate_duration, generate_gif

router = APIRouter()

def run_generate_job(job_id: str, url: str, start: float, end: float, storage_dir: str):
    """Runs synchronously in a background thread."""
    try:
        file_path = generate_gif(
            job_id=job_id,
            youtube_url=url,
            start=start,
            end=end,
            storage_dir=storage_dir,
            step_callback=lambda step: job_store.set_step(job_id, step),
        )
        job_store.complete(job_id, file_path)
    except ValueError as e:
        job_store.fail(job_id, str(e))
    except Exception as e:
        job_store.fail(job_id, "Something went wrong — please try again")

@router.post("/api/generate", status_code=202)
async def create_generate_job(
    req: GenerateRequest,
    background_tasks: BackgroundTasks,
    request: Request,
):
    if not is_youtube_url(req.url):
        raise HTTPException(400, detail="Please enter a valid YouTube URL")
    try:
        validate_duration(req.start, req.end)
    except ValueError as e:
        raise HTTPException(400, detail=str(e))

    storage_dir = request.app.state.settings.storage_dir
    job_id = job_store.create(req.url, req.start, req.end)
    background_tasks.add_task(run_generate_job, job_id, req.url, req.start, req.end, storage_dir)
    return {"job_id": job_id}

@router.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str, request: Request):
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(404, detail="Job not found")

    gif_url = None
    if job["status"] == "done" and job["file_path"]:
        # Convert absolute storage path to URL path
        storage_dir = request.app.state.settings.storage_dir
        rel = job["file_path"].replace(storage_dir, "").lstrip("/")
        gif_url = f"/static/{rel}"

    return JobResponse(
        status=job["status"],
        step=job["step"],
        gif_url=gif_url,
        error=job["error"],
    )
