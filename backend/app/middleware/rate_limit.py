"""
Simple sliding-window rate limiter stored in-memory.
For multi-instance deploys → replace with Redis.
"""
import time
from collections import defaultdict, deque

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rpm: int = None):
        super().__init__(app)
        self.rpm = rpm or settings.RATE_LIMIT_RPM
        self.window = 60  # seconds
        self._buckets: dict[str, deque] = defaultdict(deque)

    def _get_ip(self, request: Request) -> str:
        # Respect X-Forwarded-For (Railway/Render set this)
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        # Only rate-limit API processing endpoints
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        ip = self._get_ip(request)
        now = time.time()
        bucket = self._buckets[ip]

        # Evict timestamps outside the window
        while bucket and bucket[0] < now - self.window:
            bucket.popleft()

        if len(bucket) >= self.rpm:
            raise HTTPException(
                status_code=429,
                detail=f"Trop de requêtes. Limite : {self.rpm} opérations/minute."
            )

        bucket.append(now)
        return await call_next(request)
