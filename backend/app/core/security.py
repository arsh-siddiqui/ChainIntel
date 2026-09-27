"""Security middleware: in-memory rate limiting and request size limits."""
from __future__ import annotations

import time
from collections import deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.envelope import err


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple sliding-window limiter per client IP (sufficient for single-node deployments)."""

    def __init__(self, app):
        super().__init__(app)
        self._buckets: dict[str, deque] = {}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith(("/docs", "/redoc", "/openapi.json")) or request.method == "OPTIONS":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        bucket = self._buckets.setdefault(client_ip, deque())
        window = settings.rate_limit_window_seconds
        while bucket and now - bucket[0] > window:
            bucket.popleft()
        if len(bucket) >= settings.rate_limit_requests:
            return JSONResponse(
                status_code=429,
                content=err("RATE_LIMITED", "Too many requests. Please slow down and retry shortly."),
            )
        bucket.append(now)
        return await call_next(request)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject oversized request bodies before they are read into memory."""

    async def dispatch(self, request: Request, call_next):
        max_bytes = settings.max_upload_mb * 1024 * 1024
        content_length = request.headers.get("content-length")
        if content_length and content_length.isdigit() and int(content_length) > max_bytes:
            return JSONResponse(
                status_code=413,
                content=err(
                    "REQUEST_TOO_LARGE",
                    f"Request body exceeds the {settings.max_upload_mb} MB limit.",
                ),
            )
        return await call_next(request)
