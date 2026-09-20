"""Shared compact filter controls for dense toolbars."""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QDateEdit, QSizePolicy


def compact_filter(widget: QComboBox | QDateEdit, *, contents_length: int = 8) -> None:
    """Shrink Enterprise filters so they no longer dominate page minimum width."""
    widget.setObjectName("EnterpriseFilterCompact")
    widget.setMinimumHeight(36)
    widget.setMinimumWidth(0)
    widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    if isinstance(widget, QComboBox):
        widget.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        widget.setMinimumContentsLength(contents_length)
