from collections import defaultdict
from datetime import datetime, timezone
from fastapi import HTTPException, Request


class RateLimiter:
    def __init__(self):
        self._requests: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, max_requests: int, window_seconds: int) -> None:
        now = datetime.now(timezone.utc).timestamp()
        cutoff = now - window_seconds
        pruned = [t for t in self._requests[key] if t > cutoff]
        if len(pruned) >= max_requests:
            raise HTTPException(429, detail="Too many requests — please try again later")
        pruned.append(now)
        self._requests[key] = pruned

    def reset(self) -> None:
        """Clear all tracked request history. For use in tests only."""
        self._requests.clear()


def _get_ip(request: Request) -> str:
    """Return the real client IP, using X-Real-IP set by Nginx if present."""
    forwarded = request.headers.get("X-Real-IP")
    if forwarded:
        return forwarded
    if request.client:
        return request.client.host
    return "unknown"


rate_limiter = RateLimiter()


def limit_generate(request: Request) -> None:
    """5 GIF generation requests per IP per hour."""
    rate_limiter.check(f"generate:{_get_ip(request)}", max_requests=5, window_seconds=3600)


def limit_admin_login(request: Request) -> None:
    """10 admin login attempts per IP per hour."""
    rate_limiter.check(f"admin_login:{_get_ip(request)}", max_requests=10, window_seconds=3600)
