from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPlainTextEdit, QStackedWidget, QVBoxLayout, QWidget

from app.widgets.cards.enterprise_card import EnterpriseCard

try:
    from PySide6.QtPdf import QPdfDocument
    from PySide6.QtPdfWidgets import QPdfView
    _PDF = True
except Exception:
    QPdfDocument = None
    QPdfView = None
    _PDF = False


class PreviewPanel(EnterpriseCard):

    def __init__(self, parent=None) -> None:
        super().__init__("DashboardCard", parent)
        self.setMinimumWidth(280)
        self._pdf_doc = None

        title = QLabel("Predogled")
        title.setObjectName("SectionTitle")
        self.body.addWidget(title)

        self.name = QLabel("—")
        self.name.setObjectName("KpiValue")
        self.name.setWordWrap(True)
        self.meta = QLabel("Izberi dokument")
        self.meta.setObjectName("KpiHint")
        self.meta.setWordWrap(True)
        self.linked = QLabel("")
        self.linked.setObjectName("DetailValue")
        self.linked.setWordWrap(True)
        self.body.addWidget(self.name)
        self.body.addWidget(self.meta)
        self.body.addWidget(self.linked)

        self.stack = QStackedWidget()
        self.empty = QLabel("Predogled PDF in slik")
        self.empty.setObjectName("KpiHint")
        self.empty.setAlignment(Qt.AlignCenter)
        self.image = QLabel()
        self.image.setAlignment(Qt.AlignCenter)
        self.image.setMinimumHeight(180)
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.unsupported = QLabel("Predogled za to vrsto ni na voljo.\nOdpri datoteko.")
        self.unsupported.setObjectName("KpiHint")
        self.unsupported.setAlignment(Qt.AlignCenter)
        self.unsupported.setWordWrap(True)
        self.stack.addWidget(self.empty)
        self.stack.addWidget(self.image)
        self.stack.addWidget(self.text)
        self.stack.addWidget(self.unsupported)
        if _PDF:
            self.pdf_view = QPdfView()
            self.pdf_view.setMinimumHeight(220)
            self.stack.addWidget(self.pdf_view)
        else:
            self.pdf_view = None
        self.body.addWidget(self.stack, 1)

    def clear(self) -> None:
        self.name.setText("—")
        self.meta.setText("Izberi dokument")
        self.linked.setText("")
        self.stack.setCurrentIndex(0)

    def show_row(self, row, path: Path | None) -> None:
        if row is None:
            self.clear()
            return
        self.name.setText(str(row[2] or "—"))
        kind = "Mapa" if row[3] else (row[7] or "").upper()
        size = _size(row[8]) if not row[3] else "—"
        created = str(row[13] or "")[:19].replace("T", " ")
        self.meta.setText(f"{kind} · {size} · {created}")
        module = str(row[10] or "").strip()
        label = str(row[12] or "").strip()
        linked = f"{module}: {label}" if module or label else "Ni povezave"
        self.linked.setText(f"Povezano z: {linked}\nLastnik: {row[9] or '—'}")
        if row[3]:
            self.stack.setCurrentWidget(self.empty)
            return
        if path is None or not Path(path).exists():
            self.stack.setCurrentWidget(self.unsupported)
            return
        kind_key = str(row[7] or "")
        if kind_key in ("png", "jpg"):
            from app.core.thumbs import cached_pixmap
            pix = cached_pixmap(Path(path), 260)
            if not pix.isNull():
                self.image.setPixmap(pix)
                self.stack.setCurrentWidget(self.image)
                return
        if kind_key == "txt":
            try:
                self.text.setPlainText(path.read_text(encoding="utf-8", errors="replace")[:8000])
            except OSError:
                self.text.setPlainText("Datoteke ni mogoče prebrati.")
            self.stack.setCurrentWidget(self.text)
            return
        if kind_key == "pdf" and _PDF and self.pdf_view is not None:
            self._pdf_doc = QPdfDocument(self)
            self._pdf_doc.load(str(path))
            self.pdf_view.setDocument(self._pdf_doc)
            self.stack.setCurrentWidget(self.pdf_view)
            return
        self.stack.setCurrentWidget(self.unsupported)


def _size(value) -> str:
    try:
        size = int(value or 0)
    except (TypeError, ValueError):
        return "0 B"
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"
