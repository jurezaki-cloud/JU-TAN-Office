"""Zaporedna vrsta opravil z omejenim ponovnim poskusom."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from typing import Any


class Job:
    def __init__(self, key: str, fn: Callable[..., Any], kwargs: dict | None = None) -> None:
        self.key = key
        self.fn = fn
        self.kwargs = kwargs or {}
        self.retries = 0


class JobQueue:
    def __init__(self, max_retries: int = 2) -> None:
        self.max_retries = max_retries
        self._pending: deque[Job] = deque()

    def push(self, key: str, fn: Callable[..., Any], **kwargs: Any) -> None:
        self._pending.append(Job(key, fn, kwargs))

    def run_all(self) -> list[dict]:
        results: list[dict] = []
        while self._pending:
            job = self._pending.popleft()
            try:
                output = job.fn(**job.kwargs)
                results.append({
                    "key": job.key,
                    "ok": True,
                    "output": output,
                    "retry_count": job.retries,
                })
            except Exception as exc:
                job.retries += 1
                if job.retries <= self.max_retries:
                    self._pending.append(job)
                else:
                    results.append({
                        "key": job.key,
                        "ok": False,
                        "error": str(exc),
                        "retry_count": job.retries,
                    })
        return results


job_queue = JobQueue()
