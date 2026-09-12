"""Enoten odziven dialog — velikost po vsebini, scroll, footer."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.ui.icons import apply_button_icon

from app.core.ui.sizes import (
    FOOTER_HEIGHT,
    LAYOUT_SPACING,
    OUTER_MARGIN,
    SIZE_MIN_WIDTH,
    apply_dialog_table,
    available_rect,
    fit_size,
)
from app.core.ui.window_state import remember_layout


class EnterpriseDialog(QDialog):
    """Header + scroll (form/table) + footer. Velikost po vsebini, nikoli fullscreen."""

    def __init__(
        self,
        parent=None,
        *,
        title: str = "",
        heading: str | None = None,
        size: str = "MEDIUM",
        state_key: str | None = None,
        save_text: str = "Shrani",
        cancel_text: str = "Prekliči",
        show_footer: bool = True,
    ) -> None:
        super().__init__(parent)
        self._preset = (size or "MEDIUM").upper()
        self._fitted = False
        self._snapshot = None
        self.setModal(True)
        self.setSizeGripEnabled(True)
        if title:
            self.setWindowTitle(title)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._header = QWidget()
        self._header.setObjectName("DialogHeader")
        header_layout = QVBoxLayout(self._header)
        header_layout.setContentsMargins(OUTER_MARGIN, OUTER_MARGIN, OUTER_MARGIN, 8)
        header_layout.setSpacing(0)
        self.heading = QLabel(heading or title)
        self.heading.setObjectName("DialogTitle")
        header_layout.addWidget(self.heading)
        root.addWidget(self._header)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("DialogScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        inner = QWidget()
        inner.setObjectName("DialogBody")
        self.body = QVBoxLayout(inner)
        self.body.setContentsMargins(OUTER_MARGIN, 0, OUTER_MARGIN, OUTER_MARGIN)
        self.body.setSpacing(LAYOUT_SPACING)
        self.body.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(inner)
        root.addWidget(self.scroll, 1)

        self.footer = QWidget()
        self.footer.setObjectName("DialogFooter")
        self.footer.setFixedHeight(FOOTER_HEIGHT)
        self.footer_layout = QHBoxLayout(self.footer)
        self.footer_layout.setContentsMargins(OUTER_MARGIN, 0, OUTER_MARGIN, 0)
        self.footer_layout.setSpacing(8)
        self.footer_layout.addStretch()
        self.btn_cancel = QPushButton(cancel_text)
        self.btn_cancel.setObjectName("SecondaryButton")
        self.btn_save = QPushButton(save_text)
        self.btn_save.setObjectName("PrimaryButton")
        for button in (self.btn_cancel, self.btn_save):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(36)
        self.btn_save.setDefault(True)
        self.btn_save.setAutoDefault(True)
        apply_button_icon(self.btn_cancel, "cancel")
        apply_button_icon(self.btn_save, "save")
        self.footer_layout.addWidget(self.btn_cancel)
        self.footer_layout.addWidget(self.btn_save)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self.accept)
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.btn_save.click)
        if not show_footer:
            self.footer.hide()
        root.addWidget(self.footer)

        min_w = SIZE_MIN_WIDTH.get(self._preset, 520)
        self.resize(min_w, 360)
        self.setMinimumSize(400, 280)
        self._apply_screen_max()
        self._center()
        if state_key:
            remember_layout(self, state_key, geometry=False)

    def set_heading(self, text: str) -> None:
        self.heading.setText(text)

    def bind_save(self, callback: Callable[[], None]) -> None:
        try:
            self.btn_save.clicked.disconnect()
        except TypeError:
            pass
        self.btn_save.clicked.connect(callback)

    def bind_table(self, table: QTableView) -> None:
        apply_dialog_table(table)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._fitted:
            self._fitted = True
            QTimer.singleShot(0, self._after_show)

    def _after_show(self) -> None:
        self.fit_to_content()
        self._focus_first()
        self._snapshot = self._form_snapshot()

    def _focus_first(self) -> None:
        inner = self.scroll.widget()
        if inner is None:
            return
        for widget in inner.findChildren(QWidget):
            if isinstance(widget, (QLineEdit, QComboBox, QDateEdit, QAbstractSpinBox, QTextEdit)) and widget.isEnabled():
                widget.setFocus(Qt.OtherFocusReason)
                return

    def _form_snapshot(self) -> tuple:
        values = []
        inner = self.scroll.widget()
        if inner is None:
            return tuple()
        for widget in inner.findChildren(QWidget):
            if isinstance(widget, QLineEdit):
                values.append(widget.text())
            elif isinstance(widget, QTextEdit):
                values.append(widget.toPlainText())
            elif isinstance(widget, QComboBox):
                values.append(widget.currentText())
            elif isinstance(widget, QDateEdit):
                values.append(widget.date().toString(Qt.ISODate))
            elif isinstance(widget, QAbstractSpinBox):
                values.append(widget.text())
        return tuple(values)

    def _is_dirty(self) -> bool:
        if self._snapshot is None:
            return False
        return self._form_snapshot() != self._snapshot

    def reject(self) -> None:
        if self._is_dirty() and self.btn_save.isVisible():
            reply = QMessageBox.question(
                self,
                "Neshranjene spremembe",
                "Imate neshranjene spremembe. Želite zapreti brez shranjevanja?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
        super().reject()

    def fit_to_content(self) -> None:
        """Po show() prilagodi okno vsebini (max ~90 % × 85 % zaslona)."""
        try:
            inner = self.scroll.widget()
            if inner is None:
                return
            for index in range(self.body.count()):
                self.body.setStretch(index, 0)
            for table in inner.findChildren(QTableView):
                apply_dialog_table(table)
            inner.adjustSize()
            layout = inner.layout()
            hint = layout.sizeHint() if layout is not None else inner.sizeHint()
            header_h = max(self._header.sizeHint().height(), 48)
            footer_h = FOOTER_HEIGHT if self.footer.isVisible() else 0
            min_w = SIZE_MIN_WIDTH.get(self._preset, 520)
            width = max(min_w, hint.width() + 16)
            height = header_h + hint.height() + footer_h + 8
            fitted = fit_size(QSize(width, height), available_rect(self))
            self._apply_screen_max()
            self.resize(fitted)
            self._center()
        except Exception:
            pass

    def _apply_screen_max(self) -> None:
        area = available_rect(self)
        self.setMaximumSize(
            max(400, min(int(area.width() * 0.90), area.width() - 48)),
            max(280, min(int(area.height() * 0.85), area.height() - 48)),
        )

    def _center(self) -> None:
        try:
            screen = self.screen() or QGuiApplication.primaryScreen()
            if screen is None:
                return
            area = screen.availableGeometry()
            frame = self.frameGeometry()
            frame.moveCenter(area.center())
            self.move(frame.topLeft())
        except Exception:
            pass
