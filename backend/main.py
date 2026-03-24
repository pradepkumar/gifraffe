import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import load_settings
from database import init_db
from storage import ensure_storage_dirs
from cleanup import start_cleanup_task

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_settings()
    app.state.settings = settings
    init_db(settings.db_path)
    ensure_storage_dirs(settings.storage_dir)
    cleanup_task = start_cleanup_task(settings)
    yield
    cleanup_task.cancel()

app = FastAPI(title="Gifraffe", lifespan=lifespan)

# Import and register routers (added as routes are built)
from routes.generate import router as generate_router
from routes.submit import router as submit_router
from routes.gifs import router as gifs_router
from routes.admin import router as admin_router

app.include_router(generate_router)
app.include_router(submit_router)
app.include_router(gifs_router)
app.include_router(admin_router)
