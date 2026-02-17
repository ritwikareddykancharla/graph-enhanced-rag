"""Lightweight retry helper for transient operations."""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")


async def retry_async(
    func: Callable[[], Awaitable[T]],
    retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 4.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    attempt = 0
    delay = base_delay

    while True:
        try:
            return await func()
        except exceptions:
            attempt += 1
            if attempt > retries:
                raise
            await asyncio.sleep(delay)
            delay = min(delay * 2, max_delay)
