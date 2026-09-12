"""TESTI Automation Engine."""

from datetime import datetime

from app.modules.automation.automation_controller import AutomationController
from app.modules.automation.automation_repository import automation_repository
from app.modules.automation.job_queue import JobQueue
from app.modules.automation.rule_engine import evaluate_conditions, eval_custom, rule_engine
from app.modules.automation.scheduler import cron_matches, is_due
from app.modules.automation.automation_service import automation_service


def _rule(**overrides):
    data = {
        "name": "T026 pravilo",
        "description": "test",
        "trigger_key": "manual",
        "enabled": True,
        "priority": 10,
        "schedule_kind": "none",
        "schedule_value": "",
        "conditions": [],
        "actions": [{"action_key": "send_notification", "config": {"message": "ok"}}],
    }
    data.update(overrides)
    return data


def test_rule_engine_and_or_not():
    context = {"invoice_total": 150, "country": "SI"}
    ands = [
        {"join_op": "AND", "negate": False, "field": "invoice_total", "operator": "gt", "value": "100"},
        {"join_op": "AND", "negate": False, "field": "country", "operator": "eq", "value": "SI"},
    ]
    assert evaluate_conditions(ands, context)
    mixed = [
        {"join_op": "AND", "negate": False, "field": "invoice_total", "operator": "gt", "value": "999"},
        {"join_op": "OR", "negate": False, "field": "country", "operator": "eq", "value": "SI"},
    ]
    assert evaluate_conditions(mixed, context)
    negated = [{"join_op": "AND", "negate": True, "field": "country", "operator": "eq", "value": "DE"}]
    assert evaluate_conditions(negated, context)
    assert eval_custom("invoice_total > 100 and country == 'SI'", context)
    rule = {"id": 1, "enabled": True, "trigger_key": "invoice_created", "priority": 1, "conditions": ands}
    assert rule_engine.matching([rule], "invoice_created", context)
    assert not rule_engine.matching([rule], "manual", context)


def test_scheduler_daily_weekly_cron():
    now = datetime(2026, 9, 12, 10, 0, 0)
    rule = {
        "enabled": True,
        "trigger_key": "scheduled",
        "schedule_kind": "daily",
        "schedule_value": "09:00",
        "last_run_at": None,
    }
    assert is_due(rule, now)
    rule["last_run_at"] = "2026-09-12T09:05:00"
    assert not is_due(rule, now)
    weekly = {
        "enabled": True,
        "trigger_key": "scheduled",
        "schedule_kind": "weekly",
        "schedule_value": "SAT 09:00",
        "last_run_at": None,
    }
    assert is_due(weekly, now)
    assert cron_matches("0 10 * * 5", now)
    assert not cron_matches("0 8 * * *", now)


def test_job_queue_retry():
    queue = JobQueue(max_retries=1)
    state = {"n": 0}

    def boom():
        state["n"] += 1
        if state["n"] < 2:
            raise ValueError("fail")
        return "ok"

    queue.push("x", boom)
    results = queue.run_all()
    assert results[0]["ok"] is True
    assert results[0]["retry_count"] == 1


def test_repository_search_filter_and_log():
    rule_id = automation_repository.save_rule(_rule(name="Iskanje T026"))
    rows = automation_repository.list_rules(query="Iskanje T026")
    assert any(row[0] == rule_id for row in rows)
    filtered = automation_repository.list_rules(trigger="manual", enabled="on")
    assert any(row[0] == rule_id for row in filtered)
    off = automation_repository.list_rules(enabled="off")
    assert all(row[0] != rule_id for row in off)
    automation_repository.set_enabled(rule_id, False)
    assert automation_repository.get_rule(rule_id)["enabled"] is False
    copy_id = automation_service.duplicate(rule_id)
    assert copy_id != rule_id
    result = automation_service.run_now(copy_id)
    assert result["result"] == "success"
    logs = automation_repository.list_logs(query="kopija", result="success")
    assert logs
    automation_repository.delete_rule(rule_id)
    automation_repository.delete_rule(copy_id)


def test_controller_export(tmp_path):
    controller = AutomationController()
    rule_id = controller.save(_rule(name="Export T026"))
    path = tmp_path / "automation.xlsx"
    controller.export_excel(path, controller.rules(query="Export T026"))
    assert path.exists()
    controller.delete(rule_id)
