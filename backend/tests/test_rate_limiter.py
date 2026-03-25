import datetime
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from rate_limiter import RateLimiter, limit_generate


def test_allows_requests_under_limit():
    limiter = RateLimiter()
    for _ in range(5):
        limiter.check("key:1.2.3.4", max_requests=5, window_seconds=3600)


def test_blocks_on_limit_exceeded():
    limiter = RateLimiter()
    for _ in range(5):
        limiter.check("key:1.2.3.4", max_requests=5, window_seconds=3600)
    with pytest.raises(HTTPException) as exc_info:
        limiter.check("key:1.2.3.4", max_requests=5, window_seconds=3600)
    assert exc_info.value.status_code == 429


def test_different_keys_are_independent():
    limiter = RateLimiter()
    for _ in range(5):
        limiter.check("key:1.2.3.4", max_requests=5, window_seconds=3600)
    # Different IP should not be blocked
    limiter.check("key:5.6.7.8", max_requests=5, window_seconds=3600)


def test_expired_requests_do_not_count():
    limiter = RateLimiter()
    old_ts = datetime.datetime.now(datetime.timezone.utc).timestamp() - 3601
    limiter._requests["key:1.2.3.4"] = [old_ts] * 5
    # Should not be blocked — all 5 requests are outside the window
    limiter.check("key:1.2.3.4", max_requests=5, window_seconds=3600)


def test_error_message_is_user_friendly():
    limiter = RateLimiter()
    for _ in range(5):
        limiter.check("key:1.2.3.4", max_requests=5, window_seconds=3600)
    with pytest.raises(HTTPException) as exc_info:
        limiter.check("key:1.2.3.4", max_requests=5, window_seconds=3600)
    assert "try again" in exc_info.value.detail.lower()


def test_get_ip_handles_missing_client():
    request = MagicMock()
    request.headers.get.return_value = None
    request.client = None
    # Should not raise — falls back to "unknown"
    limit_generate(request)
