"""Zapis izvajanja pravil."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.modules.automation.automation_repository import automation_repository


class ExecutionLog:
    def record(
        self,
        *,
        rule: dict,
        trigger: str,
        started: datetime,
        ended: datetime,
        result: str,
        user: str,
        error: str = "",
        retry_count: int = 0,
        context: dict | None = None,
        fingerprint: str = "",
    ) -> int:
        duration = int((ended - started).total_seconds() * 1000)
        return automation_repository.add_log({
            "rule_id": rule.get("id"),
            "rule_name": rule.get("name"),
            "trigger_key": trigger,
            "fingerprint": fingerprint,
            "started_at": started.isoformat(timespec="seconds"),
            "ended_at": ended.isoformat(timespec="seconds"),
            "duration_ms": max(duration, 0),
            "result": result,
            "user_name": user,
            "error_message": error,
            "retry_count": retry_count,
            "context": context or {},
        })

    def list(self, query: str = "", result: str = "all") -> list:
        return automation_repository.list_logs(query=query, result=result)

    def already_succeeded(self, rule_id: int, fingerprint: str, day: str) -> bool:
        if not fingerprint:
            return False
        return automation_repository.logged_today(rule_id, fingerprint, day)


execution_log = ExecutionLog()
