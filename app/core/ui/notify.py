"""Kratka obvestila — toast namesto MessageBox za uspeh."""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from app.core.ui.toast import show_toast


def toast(context: QWidget | None, message: str, kind: str = "success") -> None:
    show_toast(context, message, kind)


def toast_info(context: QWidget | None, message: str) -> None:
    show_toast(context, message, "info")
