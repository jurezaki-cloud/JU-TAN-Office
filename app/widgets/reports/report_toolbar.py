from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget


class ReportToolbar(QWidget):
    refresh_clicked = Signal()
    pdf_clicked = Signal()
    excel_clicked = Signal()
    csv_clicked = Signal()
    print_clicked = Signal()
    more_clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ReportToolbar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.btn_refresh = QPushButton("Osveži")
        self.btn_pdf = QPushButton("PDF")
        self.btn_excel = QPushButton("Excel")
        self.btn_csv = QPushButton("CSV")
        self.btn_print = QPushButton("Natisni")
        self.btn_more = QPushButton("Naloži več")
        self.btn_refresh.setObjectName("PrimaryButton")
        for button in (self.btn_pdf, self.btn_excel, self.btn_csv, self.btn_print, self.btn_more):
            button.setObjectName("SecondaryButton")
        for button in (
            self.btn_refresh, self.btn_pdf, self.btn_excel,
            self.btn_csv, self.btn_print, self.btn_more,
        ):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(36)
            layout.addWidget(button)
        layout.addStretch()

        self.btn_refresh.clicked.connect(self.refresh_clicked.emit)
        self.btn_pdf.clicked.connect(self.pdf_clicked.emit)
        self.btn_excel.clicked.connect(self.excel_clicked.emit)
        self.btn_csv.clicked.connect(self.csv_clicked.emit)
        self.btn_print.clicked.connect(self.print_clicked.emit)
        self.btn_more.clicked.connect(self.more_clicked.emit)
