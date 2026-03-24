import subprocess
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

def build_ffmpeg_command(video_path: Path, start: float, end: float, output_path: Path) -> list[str]:
    duration = end - start
    return [
        "ffmpeg", "-y",
        "-i", str(video_path),
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
    validate_duration(start, end)
    import yt_dlp
    from yt_dlp.utils import download_range_func

    temp_dir = Path(storage_dir) / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_video = temp_dir / f"{job_id}.mp4"
    output_path = temp_dir / f"{job_id}.gif"

    # Step 1: Download just the needed clip segment
    step_callback("Downloading")
    ydl_opts = {
        "format": "bestvideo[height<=480][ext=mp4]/bestvideo[height<=480]/bestvideo",
        "outtmpl": str(temp_video),
        "quiet": True,
        "no_warnings": True,
        "download_ranges": download_range_func(None, [(start, end)]),
        "force_keyframes_at_cuts": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
    except Exception as e:
        raise RuntimeError(f"Video unavailable or private: {e}")

    if not temp_video.exists():
        raise RuntimeError("Download failed — please try again")

    # Step 2: Extract clip
    step_callback("Extracting clip")

    # Step 3: Convert to GIF
    step_callback("Converting to GIF")
    cmd = build_ffmpeg_command(temp_video, start, end, output_path)
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=120)
    except subprocess.TimeoutExpired:
        raise RuntimeError("Generation timed out — please try again")
    finally:
        temp_video.unlink(missing_ok=True)

    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode(errors="replace")[-500:])

    # Check file size
    size = output_path.stat().st_size
    if size > MAX_FILE_SIZE_BYTES:
        output_path.unlink()
        raise ValueError("GIF is too large — try a shorter clip")

    return str(output_path)
