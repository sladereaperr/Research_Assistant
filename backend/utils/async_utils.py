# backend/utils/async_utils.py
import asyncio
from typing import Any

def is_awaitable(obj: Any) -> bool:
    # asyncio.iscoroutine will return True for coro objects.
    # Also accept objects implementing __await__ (like asyncio.Future, etc.)
    return asyncio.iscoroutine(obj) or hasattr(obj, "__await__")

async def maybe_await(value_or_coro: Any):
    """
    If 'value_or_coro' is awaitable, await it and return the result.
    Otherwise return it as-is.
    """
    if is_awaitable(value_or_coro):
        return await value_or_coro
    return value_or_coro
