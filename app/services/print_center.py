from __future__ import annotations

from html import escape
from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QPainter, QTextDocument
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter, QPrintPreviewDialog
from PySide6.QtWidgets import QMessageBox, QWidget


class PrintCenter:
    """Single printing gateway for JU-TAN Office."""

    def _printer(self) -> QPrinter:
        printer = QPrinter(QPrinter.HighResolution)
        printer.setFullPage(False)
        return printer

    def print_pdf(self, parent: QWidget | None, path: Path | str) -> bool:
        self._require_print()
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Dokument ne obstaja: {path}")
        printer = self._printer()
        dialog = QPrintDialog(printer, parent)
        dialog.setWindowTitle("JU-TAN Print Center — Tiskanje")
        if dialog.exec() != QPrintDialog.Accepted:
            return False
        self._paint_pdf(printer, path)
        self._audit(path)
        return True
    def preview_pdf(self, parent: QWidget | None, path: Path | str) -> bool:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Dokument ne obstaja: {path}")
        printer = self._printer()
        preview = QPrintPreviewDialog(printer, parent)
        preview.setWindowTitle("JU-TAN Print Center — Predogled tiskanja")
        preview.resize(1100, 800)
        preview.paintRequested.connect(lambda device: self._paint_pdf(device, path))
        preview.exec()
        return True

    def print_html(self, parent: QWidget | None, html: str, title: str = "JU-TAN Office") -> bool:
        self._require_print()
        printer = self._printer()
        dialog = QPrintDialog(printer, parent)
        dialog.setWindowTitle(f"JU-TAN Print Center — {title}")
        if dialog.exec() != QPrintDialog.Accepted:
            return False
        document = QTextDocument()
        document.setHtml(html)
        document.print_(printer)
        self._audit(title)
        return True

    def preview_html(self, parent: QWidget | None, html: str, title: str = "JU-TAN Office") -> bool:
        printer = self._printer()
        preview = QPrintPreviewDialog(printer, parent)
        preview.setWindowTitle(f"JU-TAN Print Center — {title}")
        preview.resize(1100, 800)
        def paint(device):
            document = QTextDocument()
            document.setHtml(html)
            document.print_(device)
        preview.paintRequested.connect(paint)
        preview.exec()
        return True
    def _paint_pdf(self, printer: QPrinter, path: Path) -> None:
        pdf = QPdfDocument()
        if pdf.load(str(path)) != QPdfDocument.Error.None_:
            raise RuntimeError("PDF dokumenta ni bilo mogoče pripraviti za tisk.")
        painter = QPainter(printer)
        if not painter.isActive():
            raise RuntimeError("Tiskalnika ni bilo mogoče zagnati.")
        try:
            for page in range(pdf.pageCount()):
                if page:
                    printer.newPage()
                rect = printer.pageRect(QPrinter.DevicePixel)
                image = pdf.render(page, QSize(rect.width(), rect.height()))
                painter.drawImage(rect, image)
        finally:
            painter.end()
            pdf.close()

    @staticmethod
    def table_html(title: str, headers: list[str], rows) -> str:
        head = "".join(f"<th>{escape(str(value))}</th>" for value in headers)
        body = "".join(
            "<tr>" + "".join(f"<td>{escape(str(value or ''))}</td>" for value in row) + "</tr>"
            for row in rows
        )
        return f"""<html><head><style>
        body {{ font-family: 'Segoe UI'; font-size: 9pt; color: #172033; }}
        h1 {{ font-size: 18pt; margin-bottom: 14px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ text-align: left; background: #eef2f5; padding: 7px; border-bottom: 2px solid #24a06b; }}
        td {{ padding: 6px 7px; border-bottom: 1px solid #d9dee5; }}
        </style></head><body><h1>{escape(title)}</h1><table><thead><tr>{head}</tr></thead>
        <tbody>{body}</tbody></table></body></html>"""

    @staticmethod
    def _require_print() -> None:
        from app.core.permissions import require
        require("print")

    @staticmethod
    def _audit(subject) -> None:
        from app.core.permissions import audit
        audit("print", str(subject))


print_center = PrintCenter()
