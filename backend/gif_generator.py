import subprocess
import os
from pathlib import Path
from typing import Callable

MAX_DURATION_SECONDS = 10.0
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB

def is_youtube_url(url: str) -> bool:
    return (
        "youtube.com/watch" in url or
        "youtu.be/" in url
    )

def validate_duration(start: float, end: float) -> None:
    if end <= start:
        raise ValueError("End time must be after start time")
    if (end - start) > MAX_DURATION_SECONDS:
        raise ValueError("Maximum clip length is 10 seconds")

def build_ffmpeg_command(video_url: str, start: float, end: float, output_path: Path) -> list[str]:
    duration = end - start
    return [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", video_url,
        "-t", str(duration),
        "-filter_complex",
        "[0:v] fps=12,scale=480:-1:flags=lanczos,split [s0][s1];"
        " [s0] palettegen=max_colors=256:stats_mode=diff [p];"
        " [s1][p] paletteuse=dither=bayer [out]",
        "-map", "[out]",
        str(output_path),
    ]

def generate_gif(
    job_id: str,
    youtube_url: str,
    start: float,
    end: float,
    storage_dir: str,
    step_callback: Callable[[str], None],
) -> str:
    """
    Returns the file path of the generated GIF relative to storage_dir.
    Raises ValueError on user-fixable errors, RuntimeError on system errors.
    """
    import yt_dlp

    output_path = Path(storage_dir) / "temp" / f"{job_id}.gif"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Step 1: Get direct video stream URL
    step_callback("Downloading")
    ydl_opts = {
        "format": "best[height<=480][ext=mp4]/best[height<=480]/best",
        "quiet": True,
        "no_warnings": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            video_url = info.get("url") or info["formats"][-1]["url"]
    except Exception as e:
        raise RuntimeError(f"Video unavailable or private: {e}")

    # Step 2: Extract clip marker (FFmpeg will seek)
    step_callback("Extracting clip")

    # Step 3: Convert to GIF
    step_callback("Converting to GIF")
    cmd = build_ffmpeg_command(video_url, start, end, output_path)
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=55)
    except subprocess.TimeoutExpired:
        raise RuntimeError("Generation timed out — please try again")

    if result.returncode != 0:
        raise RuntimeError("Something went wrong — please try again")

    # Check file size
    size = output_path.stat().st_size
    if size > MAX_FILE_SIZE_BYTES:
        output_path.unlink()
        raise ValueError("GIF is too large — try a shorter clip")

    return str(output_path)
