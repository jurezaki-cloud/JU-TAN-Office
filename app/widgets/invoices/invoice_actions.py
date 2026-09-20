from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QSizePolicy, QWidget

from app.core.ui.brand_icons import brand_icon
from app.widgets.common.filter_controls import compact_filter
from app.widgets.common.toolbar_overflow import ToolbarOverflowButton


class InvoiceActions(QWidget):
    new_clicked = Signal()
    edit_clicked = Signal()
    duplicate_clicked = Signal()
    delete_clicked = Signal()
    refresh_clicked = Signal()
    pdf_clicked = Signal()
    excel_clicked = Signal()
    import_clicked = Signal()
    filter_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("InvoiceActions")
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.filter = QComboBox()
        compact_filter(self.filter)
        self.filter.setMinimumHeight(34)
        self.filter.addItem("Vsi statusi", "all")
        self.filter.addItem("Osnutek", "Osnutek")
        self.filter.addItem("Neplačano", "Neplačano")
        self.filter.addItem("Zapadlo", "Zapadlo")
        self.filter.addItem("Plačano", "Plačano")
        self.filter.addItem("Stornirano", "Stornirano")

        self.btn_new = QPushButton("Nov račun")
        self.btn_new.setObjectName("PrimaryButton")
        self.btn_new.setIcon(brand_icon("new", color="#FFFFFF", size=14))

        self.btn_edit = QPushButton("Uredi")
        self.btn_edit.setObjectName("SecondaryButton")

        self.btn_duplicate = QPushButton("Kopiraj")
        self.btn_duplicate.setObjectName("GhostButton")

        self.btn_delete = QPushButton("Izbriši")
        self.btn_delete.setObjectName("DangerButton")

        self.btn_refresh = QPushButton("Osveži")
        self.btn_refresh.setObjectName("GhostButton")

        self.btn_pdf = QPushButton("PDF")
        self.btn_pdf.setObjectName("SecondaryButton")
        self.btn_excel = QPushButton("Excel")
        self.btn_excel.setObjectName("SecondaryButton")
        self.btn_import = QPushButton("Uvoz")
        self.btn_import.setObjectName("GhostButton")
        for hidden in (
            self.btn_duplicate,
            self.btn_pdf,
            self.btn_excel,
            self.btn_import,
            self.btn_refresh,
        ):
            hidden.hide()

        self.btn_more = ToolbarOverflowButton()
        self.btn_more.add_actions(
            (
                ("Kopiraj", self.duplicate_clicked.emit),
                ("PDF", self.pdf_clicked.emit),
                ("Excel", self.excel_clicked.emit),
                ("Uvoz", self.import_clicked.emit),
                ("Osveži", self.refresh_clicked.emit),
            )
        )

        layout.addWidget(self.filter)

        for button in (self.btn_new, self.btn_edit, self.btn_delete):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(34)
            layout.addWidget(button)
        for button in (
            self.btn_duplicate,
            self.btn_pdf,
            self.btn_excel,
            self.btn_import,
            self.btn_refresh,
        ):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(34)
        layout.addWidget(self.btn_more)

        self.btn_new.clicked.connect(self.new_clicked.emit)
        self.btn_edit.clicked.connect(self.edit_clicked.emit)
        self.btn_duplicate.clicked.connect(self.duplicate_clicked.emit)
        self.btn_delete.clicked.connect(self.delete_clicked.emit)
        self.btn_pdf.clicked.connect(self.pdf_clicked.emit)
        self.btn_excel.clicked.connect(self.excel_clicked.emit)
        self.btn_import.clicked.connect(self.import_clicked.emit)
        self.btn_refresh.clicked.connect(self.refresh_clicked.emit)
        self.filter.currentIndexChanged.connect(
            lambda: self.filter_changed.emit(self.filter.currentData())
        )
