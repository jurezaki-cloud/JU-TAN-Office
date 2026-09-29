"""Layout helpers for the responsive (breakpoint) pages."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QFrame, QLayout, QScrollArea, QWidget


class _VerticalScroll(QScrollArea):
    """Scrolls vertically only, so horizontally it still needs the content's minimum width."""

    def minimumSizeHint(self) -> QSize:
        hint = super().minimumSizeHint()
        content = self.widget()
        if content is None:
            return hint
        width = content.minimumSizeHint().width() + self.verticalScrollBar().sizeHint().width()
        return QSize(max(hint.width(), width), hint.height())


def vertical_scroll(content: QWidget) -> QScrollArea:
    """Frameless vertical scroller for a panel whose height the page cannot guarantee.

    A panel shorter than its layout's minimum is squeezed instead: QBoxLayout takes the
    shortfall from the largest item first, so a form's rows collapse to zero height.
    """
    scroll = _VerticalScroll()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    # Not a tab stop: it has no focus indicator, and Tab on its children already scrolls them into view.
    scroll.setFocusPolicy(Qt.NoFocus)
    scroll.setWidget(content)
    return scroll


def detach_widgets(layout: QLayout) -> None:
    """Remove every widget from ``layout`` so the caller can place them again.

    Not ``takeAt()`` + ``setParent()``: PySide6 never deletes the item ``takeAt()``
    returns, and while it lives Qt keeps it as the widget's registered item. The item
    the widget gets when it is re-added then keeps its first height-for-width answer
    forever, so cards overlap or leave gaps after the next content or width change.
    ``setParent()`` also hides the widgets (dropping their focus) until the layout
    shows them again.
    """
    for index in reversed(range(layout.count())):
        widget = layout.itemAt(index).widget()
        if widget is not None:
            layout.removeWidget(widget)
