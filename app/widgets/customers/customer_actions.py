from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from app.core.ui.icons import apply_button_icon


class CustomerActions(QWidget):
    new_clicked = Signal()
    edit_clicked = Signal()
    delete_clicked = Signal()
    refresh_clicked = Signal()
    excel_clicked = Signal()
    import_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("CustomerActions")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.btn_new = QPushButton("Nova stranka")
        self.btn_new.setObjectName("PrimaryButton")

        self.btn_edit = QPushButton("Uredi")
        self.btn_edit.setObjectName("SecondaryButton")

        self.btn_delete = QPushButton("Izbriši")
        self.btn_delete.setObjectName("DangerButton")

        self.btn_refresh = QPushButton("Osveži")
        self.btn_refresh.setObjectName("SecondaryButton")
        self.btn_excel = QPushButton("Excel")
        self.btn_excel.setObjectName("SecondaryButton")
        self.btn_import = QPushButton("Uvoz")
        self.btn_import.setObjectName("SecondaryButton")

        for button in (
            self.btn_new,
            self.btn_edit,
            self.btn_delete,
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
        self.btn_excel.clicked.connect(self.excel_clicked.emit)
        self.btn_import.clicked.connect(self.import_clicked.emit)
        self.btn_refresh.clicked.connect(self.refresh_clicked.emit)
        apply_button_icon(self.btn_new, "new")
        apply_button_icon(self.btn_edit, "edit")
        apply_button_icon(self.btn_delete, "delete")
        apply_button_icon(self.btn_excel, "export")
        apply_button_icon(self.btn_import, "open")
        apply_button_icon(self.btn_refresh, "refresh")
