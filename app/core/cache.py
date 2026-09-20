"""Kratek TTL predpomnilnik za pogoste poizvedbe."""

from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def ttl_cache(seconds: float = 5.0) -> Callable[[F], F]:
    """Predpomni rezultat funkcije za `seconds` sekund."""

    def decorator(fn: F) -> F:
        cache: dict[tuple, tuple[float, Any]] = {}

        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any):
            key = (args, tuple(sorted(kwargs.items())))
            now = time.monotonic()
            hit = cache.get(key)
            if hit and now - hit[0] < seconds:
                return hit[1]
            value = fn(*args, **kwargs)
            cache[key] = (now, value)
            return value

        wrapper.cache_clear = cache.clear  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    return decorator
