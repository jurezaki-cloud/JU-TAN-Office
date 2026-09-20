"""Vrednotenje pogojev pravila (AND / OR / NOT)."""

from __future__ import annotations

import ast
import operator
from typing import Any

OPS = {
    "gt": operator.gt,
    "gte": operator.ge,
    "lt": operator.lt,
    "lte": operator.le,
    "eq": operator.eq,
    "ne": operator.ne,
}


def _number(value: Any) -> float | None:
    try:
        return float(str(value).replace(",", ".").strip())
    except (TypeError, ValueError):
        return None


def _compare(left: Any, op_key: str, right: Any) -> bool:
    if op_key == "contains":
        return str(right or "").casefold() in str(left or "").casefold()
    fn = OPS.get(op_key, operator.eq)
    left_n = _number(left)
    right_n = _number(right)
    if left_n is not None and right_n is not None and op_key in OPS:
        return fn(left_n, right_n)
    return fn(str(left or "").casefold(), str(right or "").casefold())


def eval_custom(expression: str, context: dict) -> bool:
    """Omejen izraz: primerjave, and/or/not, imena iz konteksta."""
    text = (expression or "").strip()
    if not text:
        return True
    tree = ast.parse(text, mode="eval")
    return bool(_eval_node(tree.body, context))


def _eval_node(node: ast.AST, context: dict):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return context.get(node.id)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return not _eval_node(node.operand, context)
    if isinstance(node, ast.BoolOp):
        values = [_eval_node(item, context) for item in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        return any(values)
    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, context)
        for op, raw in zip(node.ops, node.comparators, strict=True):
            right = _eval_node(raw, context)
            mapping = {
                ast.Gt: "gt",
                ast.GtE: "gte",
                ast.Lt: "lt",
                ast.LtE: "lte",
                ast.Eq: "eq",
                ast.NotEq: "ne",
            }
            key = mapping.get(type(op), "eq")
            if not _compare(left, key, right):
                return False
            left = right
        return True
    raise ValueError("Nepodprt izraz.")


def evaluate_atom(condition: dict, context: dict) -> bool:
    field = condition.get("field") or ""
    if field == "custom_expression":
        ok = eval_custom(str(condition.get("value") or ""), context)
    else:
        ok = _compare(context.get(field), condition.get("operator") or "eq", condition.get("value"))
    if condition.get("negate"):
        return not ok
    return ok


def evaluate_conditions(conditions: list[dict], context: dict) -> bool:
    if not conditions:
        return True
    result = True
    for index, condition in enumerate(conditions):
        ok = evaluate_atom(condition, context)
        if index == 0:
            result = ok
        elif (condition.get("join_op") or "AND").upper() == "OR":
            result = result or ok
        else:
            result = result and ok
    return bool(result)


class RuleEngine:
    """Izbere in ovrednoti pravila za sprožilec."""

    def matching(self, rules: list[dict], trigger: str, context: dict) -> list[dict]:
        selected = [
            rule for rule in rules
            if rule.get("enabled") and rule.get("trigger_key") == trigger
        ]
        selected.sort(key=lambda item: (int(item.get("priority") or 100), int(item.get("id") or 0)))
        return [rule for rule in selected if evaluate_conditions(rule.get("conditions") or [], context)]


rule_engine = RuleEngine()
