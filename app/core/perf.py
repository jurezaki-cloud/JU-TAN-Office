"""Merjenje zagona, CPU/pomnilnik, disk — brez zunanjih odvisnosti."""

from __future__ import annotations

import gc
import logging
import os
import sys
import time
from dataclasses import dataclass, field

logger = logging.getLogger("ju-tan")


@dataclass
class PerfSpan:
    name: str
    started: float = field(default_factory=time.perf_counter)
    marks: list[tuple[str, float]] = field(default_factory=list)

    def mark(self, label: str) -> float:
        elapsed = (time.perf_counter() - self.started) * 1000
        self.marks.append((label, elapsed))
        return elapsed

    def summary(self) -> str:
        parts = [f"{label}={ms:.0f}ms" for label, ms in self.marks]
        total = (time.perf_counter() - self.started) * 1000
        return f"{self.name} total={total:.0f}ms " + " ".join(parts)


def memory_mb() -> float:
    """RSS v MB (Windows WorkingSet), sicer 0."""
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            counters = PROCESS_MEMORY_COUNTERS()
            counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            if ctypes.windll.psapi.GetProcessMemoryInfo(
                handle, ctypes.byref(counters), counters.cb
            ):
                return counters.WorkingSetSize / (1024 * 1024)
        except Exception:
            return 0.0
    try:
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform == "darwin":
            return usage / (1024 * 1024)
        return usage / 1024
    except Exception:
        return 0.0


def snapshot() -> dict:
    return {
        "memory_mb": round(memory_mb(), 2),
        "pid": os.getpid(),
        "gc_objects": len(gc.get_objects()),
    }


def collect_garbage() -> int:
    return gc.collect()


def log_snapshot(context: str) -> None:
    data = snapshot()
    logger.info(
        "Perf %s memory=%.1fMB gc_objects=%s",
        context,
        data["memory_mb"],
        data["gc_objects"],
    )
