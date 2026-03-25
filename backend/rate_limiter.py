from collections import defaultdict
from datetime import datetime, timezone
from fastapi import HTTPException, Request


class RateLimiter:
    def __init__(self):
        self._requests: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, max_requests: int, window_seconds: int) -> None:
        now = datetime.now(timezone.utc).timestamp()
        cutoff = now - window_seconds
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]
        if len(self._requests[key]) >= max_requests:
            raise HTTPException(429, detail="Too many requests — please try again later")
        self._requests[key].append(now)


def _get_ip(request: Request) -> str:
    """Return the real client IP, using X-Real-IP set by Nginx if present."""
    return request.headers.get("X-Real-IP") or request.client.host


rate_limiter = RateLimiter()


def limit_generate(request: Request) -> None:
    """5 GIF generation requests per IP per hour."""
    rate_limiter.check(f"generate:{_get_ip(request)}", max_requests=5, window_seconds=3600)


def limit_admin_login(request: Request) -> None:
    """10 admin login attempts per IP per hour."""
    rate_limiter.check(f"admin_login:{_get_ip(request)}", max_requests=10, window_seconds=3600)
