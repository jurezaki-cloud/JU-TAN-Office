"""Paginacija seznamov za tabele."""

from __future__ import annotations

from typing import Sequence, TypeVar

T = TypeVar("T")

DEFAULT_PAGE_SIZE = 50
GRID_PAGE_SIZE = 200


class IncrementalLoader:
    """Strani za virtualni seznam (LIMIT/OFFSET)."""

    def __init__(self, fetch, page_size: int = GRID_PAGE_SIZE) -> None:
        self.fetch = fetch
        self.page_size = max(1, page_size)
        self.offset = 0
        self.exhausted = False

    def first(self) -> list:
        self.offset = 0
        self.exhausted = False
        return self._take()

    def more(self) -> list:
        if self.exhausted:
            return []
        return self._take()

    def _take(self) -> list:
        rows = list(self.fetch(self.offset, self.page_size) or [])
        self.offset += len(rows)
        if len(rows) < self.page_size:
            self.exhausted = True
        return rows


def page_slice(rows: Sequence[T], page: int, size: int = DEFAULT_PAGE_SIZE) -> list[T]:
    """Vrni stran `page` (0-indeksirano) iz seznama."""
    start = max(0, page) * max(1, size)
    return list(rows[start:start + size])


def has_more(total: int, page: int, size: int = DEFAULT_PAGE_SIZE) -> bool:
    return total > (page + 1) * max(1, size)
