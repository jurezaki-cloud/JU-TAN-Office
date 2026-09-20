from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QSizePolicy, QWidget

from app.widgets.common.toolbar_overflow import ToolbarOverflowButton


class DocumentToolbar(QWidget):
    upload_clicked = Signal()
    folder_clicked = Signal()
    refresh_clicked = Signal()
    download_clicked = Signal()
    delete_clicked = Signal()
    export_clicked = Signal()
    up_clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("DocumentToolbar")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.btn_upload = QPushButton("Naloži")
        self.btn_upload.setObjectName("PrimaryButton")
        self.btn_folder = QPushButton("Nova mapa")
        self.btn_folder.setObjectName("SecondaryButton")
        self.btn_up = QPushButton("Nazaj")
        self.btn_up.setObjectName("SecondaryButton")

        # Kept for API/compat; surfaced via overflow menu.
        self.btn_refresh = QPushButton("Osveži")
        self.btn_refresh.setObjectName("SecondaryButton")
        self.btn_download = QPushButton("Prenesi")
        self.btn_download.setObjectName("SecondaryButton")
        self.btn_delete = QPushButton("Izbriši")
        self.btn_delete.setObjectName("DangerButton")
        self.btn_export = QPushButton("Izvozi seznam")
        self.btn_export.setObjectName("SecondaryButton")
        for hidden in (self.btn_refresh, self.btn_download, self.btn_delete, self.btn_export):
            hidden.hide()

        self.btn_more = ToolbarOverflowButton()
        self.btn_more.add_actions(
            (
                ("Osveži", self.refresh_clicked.emit),
                ("Prenesi", self.download_clicked.emit),
                ("Izbriši", self.delete_clicked.emit),
                ("Izvozi seznam", self.export_clicked.emit),
            )
        )

        for button in (self.btn_upload, self.btn_folder, self.btn_up):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(36)
            layout.addWidget(button)
        layout.addStretch(1)
        layout.addWidget(self.btn_more)

        self.btn_upload.clicked.connect(self.upload_clicked.emit)
        self.btn_folder.clicked.connect(self.folder_clicked.emit)
        self.btn_up.clicked.connect(self.up_clicked.emit)
        self.btn_refresh.clicked.connect(self.refresh_clicked.emit)
        self.btn_download.clicked.connect(self.download_clicked.emit)
        self.btn_delete.clicked.connect(self.delete_clicked.emit)
        self.btn_export.clicked.connect(self.export_clicked.emit)
