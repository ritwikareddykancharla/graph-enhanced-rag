"""Simple in-memory rate limiting middleware."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import Request
from fastapi.responses import JSONResponse


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.hits: Dict[str, Deque[float]] = defaultdict(deque)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        queue = self.hits[key]

        while queue and queue[0] < window_start:
            queue.popleft()

        if len(queue) >= self.max_requests:
            return False

        queue.append(now)
        return True


class RateLimitMiddleware:
    def __init__(self, app, limiter: RateLimiter) -> None:
        self.app = app
        self.limiter = limiter

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        client = request.client.host if request.client else "unknown"
        api_key = request.headers.get("x-api-key", "anonymous")
        key = f"{client}:{api_key}"

        if not self.limiter.is_allowed(key):
            response = JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "limit": self.limiter.max_requests,
                    "window_seconds": self.limiter.window_seconds,
                },
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
