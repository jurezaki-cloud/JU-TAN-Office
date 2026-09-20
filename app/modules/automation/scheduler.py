"""Razpored izvajanja (dnevno / tedensko / mesečno / cron pripravljen)."""

from __future__ import annotations

from datetime import datetime

WEEKDAYS = {
    "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6,
    "0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
}


def _parse_time(value: str) -> tuple[int, int]:
    text = (value or "00:00").strip()
    parts = text.replace(";", " ").split()
    clock = parts[-1] if parts else "00:00"
    if ":" not in clock:
        clock = "00:00"
    hour, minute = clock.split(":", 1)
    return int(hour), int(minute)


def _same_run_window(last_run: str | None, now: datetime, kind: str) -> bool:
    if not last_run:
        return False
    try:
        previous = datetime.fromisoformat(str(last_run)[:19])
    except ValueError:
        return False
    if kind == "daily":
        return previous.date() == now.date()
    if kind == "weekly":
        return previous.isocalendar()[:2] == now.isocalendar()[:2]
    if kind == "monthly":
        return (previous.year, previous.month) == (now.year, now.month)
    if kind == "cron":
        return previous.strftime("%Y-%m-%d %H:%M") == now.strftime("%Y-%m-%d %H:%M")
    return previous.date() == now.date()


def cron_matches(expr: str, now: datetime) -> bool:
    """Podpira 5 polj: minuta ura dan mesec dan-tedna (* ali številka)."""
    parts = (expr or "").split()
    if len(parts) != 5:
        return False
    minute, hour, day, month, weekday = parts
    actual = [now.minute, now.hour, now.day, now.month, now.weekday()]
    for token, value in zip(parts, actual, strict=True):
        if token in ("*", "?"):
            continue
        allowed = {int(item) for item in token.split(",") if item.isdigit()}
        if value not in allowed:
            return False
    return True


def is_due(rule: dict, now: datetime | None = None) -> bool:
    now = now or datetime.now()
    if not rule.get("enabled"):
        return False
    if (rule.get("trigger_key") or "") != "scheduled":
        return False
    kind = (rule.get("schedule_kind") or "none").lower()
    if kind in ("none", "manual"):
        return False
    value = str(rule.get("schedule_value") or "")
    if _same_run_window(rule.get("last_run_at"), now, kind):
        return False
    if kind == "cron":
        return cron_matches(value, now)
    hour, minute = _parse_time(value)
    if (now.hour, now.minute) < (hour, minute):
        return False
    if kind == "daily":
        return True
    if kind == "weekly":
        token = value.strip().split()[0].casefold() if value.strip() else str(now.weekday())
        weekday = WEEKDAYS.get(token[:3], WEEKDAYS.get(token, now.weekday()))
        return now.weekday() == weekday
    if kind == "monthly":
        day_token = value.strip().split()[0]
        try:
            day = int(day_token)
        except ValueError:
            day = 1
        return now.day == day
    return False


class AutomationScheduler:
    def due_rules(self, rules: list[dict], now: datetime | None = None) -> list[dict]:
        now = now or datetime.now()
        return [rule for rule in rules if is_due(rule, now)]


automation_scheduler = AutomationScheduler()
