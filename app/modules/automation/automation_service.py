"""Orkestracija pravil prek obstoječih service/repository slojev."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from app.core.logger import logger
from app.core.permissions import audit, require
from app.database.article_repository import article_repository
from app.database.customer_repository import customer_repository
from app.database.invoice_repository import invoice_repository
from app.database.order_repository import order_repository
from app.modules.automation.automation_repository import automation_repository
from app.modules.automation.execution_log import execution_log
from app.modules.automation.job_queue import JobQueue
from app.modules.automation.rule_engine import rule_engine
from app.modules.automation.scheduler import automation_scheduler
from app.modules.crm.crm_repository import crm_repository
from app.modules.documents.documents_repository import documents_repository
from app.modules.purchase.purchase_repository import purchase_repository
from app.modules.suppliers.suppliers_repository import suppliers_repository
from app.modules.warehouse.warehouse_service import STATUS_LOW, warehouse_service
from app.pdf.pdf_company import load_company
from app.pdf.pdf_export import pdf_export


class AutomationService:
    def __init__(self, repository=automation_repository) -> None:
        self.repository = repository
        self.engine = rule_engine
        self.scheduler = automation_scheduler
        self.log = execution_log

    def user_name(self) -> str:
        return (load_company().name or "JU-TAN").strip()

    def rules(self, query: str = "", trigger: str = "all", enabled: str = "all") -> list:
        return self.repository.list_rules(query=query, trigger=trigger, enabled=enabled)

    def get(self, rule_id: int) -> dict | None:
        return self.repository.get_rule(rule_id)

    def save(self, data: dict) -> int:
        require("write")
        audit("create", f"automation:{data.get('name')}")
        return self.repository.save_rule(data)

    def delete(self, rule_id: int) -> None:
        require("delete")
        audit("delete", f"automation:{rule_id}")
        self.repository.delete_rule(rule_id)

    def set_enabled(self, rule_id: int, enabled: bool) -> None:
        self.repository.set_enabled(rule_id, enabled)

    def duplicate(self, rule_id: int) -> int:
        rule = self.repository.get_rule(rule_id)
        if rule is None:
            raise ValueError("Pravilo ne obstaja.")
        rule.pop("id", None)
        rule["name"] = f"{rule.get('name') or 'Pravilo'} (kopija)"
        rule["enabled"] = False
        return self.save(rule)

    def kpis(self) -> dict:
        return self.repository.kpis()

    def logs(self, query: str = "", result: str = "all") -> list:
        return self.log.list(query=query, result=result)

    def dispatch(self, trigger: str, context: dict | None = None, *, user: str | None = None) -> list[dict]:
        """Javni vstop — obstoječi moduli ga lahko pokličejo brez spremembe logike."""
        context = dict(context or {})
        context.setdefault("trigger", trigger)
        results = []
        ids = [row[0] for row in self.repository.list_rules(trigger=trigger, enabled="on")]
        loaded = [self.repository.get_rule(rule_id) for rule_id in ids]
        for rule in self.engine.matching([item for item in loaded if item], trigger, context):
            results.append(self.execute_rule(rule, trigger, context, user=user))
        return results

    def run_now(self, rule_id: int, context: dict | None = None) -> dict:
        rule = self.repository.get_rule(rule_id)
        if rule is None:
            raise ValueError("Pravilo ne obstaja.")
        payload = dict(context or {})
        trigger = rule.get("trigger_key") or "manual"
        payload.setdefault("trigger", trigger)
        return self.execute_rule(rule, trigger, payload, force=True)

    def tick(self, now: datetime | None = None) -> list[dict]:
        now = now or datetime.now()
        results = []
        for row in self.repository.list_rules(enabled="on"):
            rule = self.repository.get_rule(row[0])
            if rule and self.scheduler.due_rules([rule], now):
                results.append(self.execute_rule(rule, "scheduled", {"source": "scheduler"}, force=True))
        for trigger, context in self.scan_events():
            results.extend(self.dispatch(trigger, context))
        return results

    def scan_events(self) -> list[tuple[str, dict]]:
        events: list[tuple[str, dict]] = []
        today = date.today()
        for row in invoice_repository.get_all():
            full = invoice_repository.get_by_id(row[0])
            if full is None:
                continue
            status = str(full[5] or "")
            due = str(full[4] or "")[:10]
            if status in ("Plačan", "Plačano", "Storniran"):
                continue
            try:
                if due and date.fromisoformat(due) < today:
                    events.append(("invoice_overdue", self._invoice_context(full)))
            except ValueError:
                pass
        for item in warehouse_service.stock_rows():
            if item.status == STATUS_LOW or (item.min_qty > 0 and item.qty <= item.min_qty):
                events.append((
                    "stock_below_minimum",
                    {
                        "article_id": item.article_id,
                        "product_category": item.category,
                        "warehouse": item.warehouse_id,
                        "invoice_total": 0,
                    },
                ))
        return events

    def execute_rule(
        self,
        rule: dict,
        trigger: str,
        context: dict,
        *,
        user: str | None = None,
        force: bool = False,
    ) -> dict:
        started = datetime.now()
        user = user or self.user_name()
        fingerprint = self._fingerprint(trigger, context)
        day = started.strftime("%Y-%m-%d")
        if not force and self.log.already_succeeded(int(rule["id"]), fingerprint, day):
            return {"rule_id": rule["id"], "result": "skipped"}
        if not force and not self.engine.matching([rule], trigger, context):
            # Manual run still checks conditions unless empty
            if trigger != "manual":
                return {"rule_id": rule["id"], "result": "skipped"}
        queue = JobQueue(max_retries=1)
        for action in rule.get("actions") or []:
            queue.push(
                action.get("action_key") or "send_notification",
                self._run_action,
                action_key=action.get("action_key"),
                config=action.get("config") or {},
                context=context,
            )
        if not rule.get("actions"):
            queue.push("noop", lambda **_k: "ok")
        outcomes = queue.run_all()
        failed = [item for item in outcomes if not item.get("ok")]
        retries = max((int(item.get("retry_count") or 0) for item in outcomes), default=0)
        ended = datetime.now()
        result = "failed" if failed else "success"
        error = "; ".join(item.get("error") or "" for item in failed)
        self.log.record(
            rule=rule,
            trigger=trigger,
            started=started,
            ended=ended,
            result=result,
            user=user,
            error=error,
            retry_count=retries,
            context=context,
            fingerprint=fingerprint,
        )
        self.repository.mark_run(int(rule["id"]), ended.isoformat(timespec="seconds"))
        audit("write", f"automation-run:{rule.get('name')}:{result}")
        return {"rule_id": rule["id"], "result": result, "error": error, "actions": outcomes}

    def _fingerprint(self, trigger: str, context: dict) -> str:
        for key in ("invoice_id", "article_id", "customer_id", "deal_id", "purchase_id", "order_id", "document_id"):
            if context.get(key):
                return f"{trigger}:{key}:{context[key]}"
        return f"{trigger}:generic"

    def _invoice_context(self, invoice) -> dict:
        customer = customer_repository.get_by_id(invoice[2]) if invoice[2] else None
        return {
            "invoice_id": invoice[0],
            "invoice_total": float(invoice[9] or 0),
            "invoice_status": invoice[5],
            "customer_id": invoice[2],
            "country": customer[6] if customer else "",
            "customer_category": "",
            "payment_method": "",
            "due_date": invoice[4],
        }

    def _run_action(self, action_key: str, config: dict, context: dict) -> Any:
        handlers = {
            "create_invoice": self._action_create_invoice,
            "create_purchase_order": self._action_create_po,
            "create_crm_activity": self._action_crm,
            "create_reminder": self._action_reminder,
            "reserve_inventory": self._action_reserve,
            "update_status": self._action_status,
            "generate_pdf": self._action_pdf,
            "send_email": self._action_email,
            "send_notification": self._action_notify,
            "archive_document": self._action_archive,
            "python_hook": self._action_hook,
        }
        handler = handlers.get(action_key, self._action_notify)
        return handler(config, context)

    def _action_create_invoice(self, config: dict, context: dict) -> str:
        customer_id = context.get("customer_id") or config.get("customer_id")
        if not customer_id:
            customers = customer_repository.get_all()
            if not customers:
                raise ValueError("Ni stranke za račun.")
            customer_id = customers[0][0]
        number = invoice_repository.get_next_number()
        today = date.today()
        due = today + timedelta(days=int(config.get("days") or 14))
        total = float(config.get("total") or context.get("invoice_total") or 0)
        invoice_repository.add(
            number, customer_id, today.isoformat(), due.isoformat(),
            total, 0, 0, total, config.get("notes") or "Automation",
        )
        invoice_repository.increase_counter()
        return number

    def _action_create_po(self, config: dict, context: dict) -> int:
        suppliers = suppliers_repository.get_all()
        if not suppliers:
            raise ValueError("Ni dobavitelja za nabavno naročilo.")
        supplier_id = int(config.get("supplier_id") or suppliers[0][0])
        number = config.get("number") or purchase_repository.get_next_number()
        today = date.today().isoformat()
        return purchase_repository.create(
            number, supplier_id, today, today,
            config.get("status") or "Draft",
            0, 0, 0, config.get("notes") or "Automation",
        )

    def _action_crm(self, config: dict, context: dict) -> int:
        return crm_repository.add_activity(
            customer_id=context.get("customer_id"),
            pipeline_id=context.get("deal_id"),
            type=config.get("type") or "Task",
            title=config.get("title") or "Automation",
            salesperson=self.user_name(),
            notes=config.get("notes") or "",
        )

    def _action_reminder(self, config: dict, context: dict) -> int:
        due = (date.today() + timedelta(days=int(config.get("days") or 1))).isoformat()
        return crm_repository.add_activity(
            customer_id=context.get("customer_id"),
            pipeline_id=context.get("deal_id"),
            type="Reminder",
            title=config.get("title") or "Opomnik",
            due_date=due,
            salesperson=self.user_name(),
        )

    def _action_reserve(self, config: dict, context: dict) -> str:
        article_id = context.get("article_id") or config.get("article_id")
        if not article_id:
            articles = article_repository.get_all()
            if not articles:
                raise ValueError("Ni artikla za rezervacijo.")
            article_id = articles[0][0]
        warehouse_service.add_movement(
            movement_type="Rezervacija",
            article_id=int(article_id),
            warehouse_id=str(context.get("warehouse") or config.get("warehouse") or "main"),
            quantity=float(config.get("quantity") or 1),
            user=self.user_name(),
            note="Automation",
        )
        return str(article_id)

    def _action_status(self, config: dict, context: dict) -> str:
        status = config.get("status") or "Izdan"
        if context.get("invoice_id"):
            invoice_repository.update_status(int(context["invoice_id"]), status)
            return status
        if context.get("purchase_id"):
            purchase_repository.set_status(int(context["purchase_id"]), status)
            return status
        if context.get("order_id"):
            order = order_repository.get_by_id(int(context["order_id"]))
            if order:
                order_repository.update(
                    order[0],
                    order[2],
                    order[3],
                    order[4],
                    status,
                    order[6],
                    order[7],
                    order[8],
                    order[9],
                    order[10] or "",
                )
            return status
        return status

    def _action_pdf(self, config: dict, context: dict) -> str:
        invoice_id = context.get("invoice_id") or config.get("invoice_id")
        if not invoice_id:
            return "skip"
        path = pdf_export.export_invoice(invoice_id)
        return str(path)

    def _action_email(self, config: dict, context: dict) -> str:
        logger.info("Automation email placeholder: %s", config.get("to") or context.get("email"))
        return "email-placeholder"

    def _action_notify(self, config: dict, context: dict) -> str:
        message = config.get("message") or f"Automation: {context.get('trigger')}"
        logger.info("Automation notification: %s", message)
        return message

    def _action_archive(self, config: dict, context: dict) -> int:
        document_id = context.get("document_id") or config.get("document_id")
        if document_id:
            documents_repository.update_meta(int(document_id), module="archive")
            return int(document_id)
        return documents_repository.add(
            name=config.get("name") or "Automation arhiv",
            is_folder=True,
            owner=self.user_name(),
            module="archive",
        )

    def _action_hook(self, config: dict, context: dict) -> str:
        logger.info("Python hook placeholder: %s", config.get("module") or "none")
        return "python-hook-placeholder"


automation_service = AutomationService()
