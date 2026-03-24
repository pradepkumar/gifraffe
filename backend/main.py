import os
from dotenv import load_dotenv
load_dotenv()
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from config import load_settings
from database import init_db
from storage import ensure_storage_dirs
from cleanup import start_cleanup_task

# Pre-create storage dirs at module load time so StaticFiles can mount below.
# STORAGE_DIR env var must be set before this module is imported (done by .env or test fixtures).
_storage_dir = os.environ.get("STORAGE_DIR", "storage")
for _sub in ("temp", "pending", "gifs"):
    Path(_storage_dir, _sub).mkdir(parents=True, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_settings()
    app.state.settings = settings
    init_db(settings.db_path)
    ensure_storage_dirs(settings.storage_dir)
    task = start_cleanup_task(settings)
    yield
    task.cancel()

app = FastAPI(title="Gifraffe", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount approved and temp GIF dirs as static files
app.mount("/static/gifs", StaticFiles(directory=str(Path(_storage_dir) / "gifs")), name="static_gifs")
app.mount("/static/temp", StaticFiles(directory=str(Path(_storage_dir) / "temp")), name="static_temp")

from routes.generate import router as generate_router
from routes.submit import router as submit_router
from routes.gifs import router as gifs_router
from routes.admin import router as admin_router

app.include_router(generate_router)
app.include_router(submit_router)
app.include_router(gifs_router)
app.include_router(admin_router)

# Serve built frontend (production)
FRONTEND_BUILD = Path(__file__).parent / "static_frontend"

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    index = FRONTEND_BUILD / "index.html"
    if not index.exists():
        return {"message": "Frontend not built yet — run: cd frontend && npm run build"}
    resolved = (FRONTEND_BUILD / full_path).resolve()
    if resolved.is_file() and resolved.is_relative_to(FRONTEND_BUILD.resolve()):
        return FileResponse(str(resolved))
    return FileResponse(str(index))
