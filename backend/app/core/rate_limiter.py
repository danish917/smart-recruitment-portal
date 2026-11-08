"""In-memory thread-safe rate limiter for FastAPI endpoints."""

import time
from collections import defaultdict
from threading import Lock
from typing import Callable, Dict, List
from fastapi import HTTPException, Request, status
from app.core.config import settings


class InMemoryRateLimiter:
    """Sliding-window rate limiter per client IP."""

    def __init__(self) -> None:
        self._history: Dict[str, List[float]] = defaultdict(list)
        self._lock = Lock()

    def check(self, key: str, max_requests: int, window_seconds: int = 60) -> None:
        """Check if request exceeds rate limit. Raises 429 if limit exceeded."""
        if not settings.RATE_LIMIT_ENABLED:
            return

        now = time.time()
        with self._lock:
            # Purge timestamps older than window
            cutoff = now - window_seconds
            valid_timestamps = [t for t in self._history[key] if t > cutoff]

            if len(valid_timestamps) >= max_requests:
                earliest = valid_timestamps[0]
                retry_after = max(1, int(earliest + window_seconds - now))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds}s.",
                    headers={"Retry-After": str(retry_after)},
                )

            valid_timestamps.append(now)
            self._history[key] = valid_timestamps

    def clear(self) -> None:
        """Clear all rate limit history (useful for tests)."""
        with self._lock:
            self._history.clear()


limiter = InMemoryRateLimiter()


def rate_limit(max_requests: int, window_seconds: int = 60) -> Callable:
    """FastAPI dependency to rate limit by client IP."""

    async def dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        # Forwarded-For support if running behind a reverse proxy (e.g. nginx, docker)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

        key = f"{request.url.path}:{client_ip}"
        limiter.check(key, max_requests, window_seconds)

    return dependency
