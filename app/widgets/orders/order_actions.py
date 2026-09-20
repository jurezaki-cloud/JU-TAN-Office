from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QWidget


class OrderActions(QWidget):
    new_clicked = Signal()
    edit_clicked = Signal()
    delete_clicked = Signal()
    refresh_clicked = Signal()
    pdf_clicked = Signal()
    excel_clicked = Signal()
    import_clicked = Signal()
    filter_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("OrderActions")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.filter = QComboBox()
        self.filter.setObjectName("EnterpriseFilter")
        self.filter.setMinimumHeight(36)
        self.filter.addItem("Vsi statusi", "all")
        self.filter.addItem("Osnutek", "Osnutek")
        self.filter.addItem("Potrjeno", "Potrjeno")
        self.filter.addItem("V obdelavi", "V obdelavi")
        self.filter.addItem("Dobavljeno", "Dobavljeno")
        self.filter.addItem("Preklicano", "Preklicano")

        self.btn_new = QPushButton("Novo naročilo")
        self.btn_new.setObjectName("PrimaryButton")
        self.btn_edit = QPushButton("Uredi")
        self.btn_edit.setObjectName("SecondaryButton")
        self.btn_delete = QPushButton("Izbriši")
        self.btn_delete.setObjectName("DangerButton")
        self.btn_pdf = QPushButton("PDF")
        self.btn_pdf.setObjectName("SecondaryButton")
        self.btn_excel = QPushButton("Excel")
        self.btn_excel.setObjectName("SecondaryButton")
        self.btn_import = QPushButton("Uvoz")
        self.btn_import.setObjectName("SecondaryButton")
        self.btn_refresh = QPushButton("Osveži")
        self.btn_refresh.setObjectName("SecondaryButton")

        layout.addWidget(self.filter)
        for button in (
            self.btn_new,
            self.btn_edit,
            self.btn_delete,
            self.btn_pdf,
            self.btn_excel,
            self.btn_import,
            self.btn_refresh,
        ):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(36)
            layout.addWidget(button)

        self.btn_new.clicked.connect(self.new_clicked.emit)
        self.btn_edit.clicked.connect(self.edit_clicked.emit)
        self.btn_delete.clicked.connect(self.delete_clicked.emit)
        self.btn_pdf.clicked.connect(self.pdf_clicked.emit)
        self.btn_excel.clicked.connect(self.excel_clicked.emit)
        self.btn_import.clicked.connect(self.import_clicked.emit)
        self.btn_refresh.clicked.connect(self.refresh_clicked.emit)
        self.filter.currentIndexChanged.connect(
            lambda: self.filter_changed.emit(self.filter.currentData())
        )
