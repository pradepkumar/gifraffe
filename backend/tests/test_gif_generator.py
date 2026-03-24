import pytest

def test_is_youtube_url_accepts_watch_url():
    from gif_generator import is_youtube_url
    assert is_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True

def test_is_youtube_url_accepts_short_url():
    from gif_generator import is_youtube_url
    assert is_youtube_url("https://youtu.be/dQw4w9WgXcQ") is True

def test_is_youtube_url_rejects_non_youtube():
    from gif_generator import is_youtube_url
    assert is_youtube_url("https://vimeo.com/123") is False
    assert is_youtube_url("https://example.com") is False
    assert is_youtube_url("not-a-url") is False

def test_validate_duration_accepts_valid():
    from gif_generator import validate_duration
    validate_duration(0.0, 5.0)   # 5 seconds — ok
    validate_duration(10.0, 20.0)  # 10 seconds — ok (at limit)

def test_validate_duration_rejects_too_long():
    from gif_generator import validate_duration
    with pytest.raises(ValueError, match="Maximum clip length is 10 seconds"):
        validate_duration(0.0, 11.0)

def test_validate_duration_rejects_inverted():
    from gif_generator import validate_duration
    with pytest.raises(ValueError, match="End time must be after start time"):
        validate_duration(10.0, 5.0)

def test_build_ffmpeg_command(tmp_path):
    from gif_generator import build_ffmpeg_command
    output = tmp_path / "out.gif"
    cmd = build_ffmpeg_command("http://video-url", 5.0, 10.0, output)
    assert cmd[0] == "ffmpeg"
    assert "-ss" in cmd
    assert "5.0" in cmd
    assert "-t" in cmd
    assert "5.0" in cmd  # duration = end - start
    assert str(output) in cmd
