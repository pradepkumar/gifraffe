import shutil
from pathlib import Path

def ensure_storage_dirs(storage_dir: str) -> None:
    for sub in ("temp", "pending", "gifs"):
        Path(storage_dir, sub).mkdir(parents=True, exist_ok=True)

def move_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))

def delete_file(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass
