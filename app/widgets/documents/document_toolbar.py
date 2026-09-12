from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget


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

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.btn_upload = QPushButton("Upload")
        self.btn_upload.setObjectName("PrimaryButton")
        self.btn_folder = QPushButton("New Folder")
        self.btn_folder.setObjectName("SecondaryButton")
        self.btn_up = QPushButton("Nazaj")
        self.btn_up.setObjectName("SecondaryButton")
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setObjectName("SecondaryButton")
        self.btn_download = QPushButton("Download")
        self.btn_download.setObjectName("SecondaryButton")
        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setObjectName("DangerButton")
        self.btn_export = QPushButton("Export List")
        self.btn_export.setObjectName("SecondaryButton")

        for button in (
            self.btn_upload,
            self.btn_folder,
            self.btn_up,
            self.btn_refresh,
            self.btn_download,
            self.btn_delete,
            self.btn_export,
        ):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(36)
            layout.addWidget(button)

        self.btn_upload.clicked.connect(self.upload_clicked.emit)
        self.btn_folder.clicked.connect(self.folder_clicked.emit)
        self.btn_up.clicked.connect(self.up_clicked.emit)
        self.btn_refresh.clicked.connect(self.refresh_clicked.emit)
        self.btn_download.clicked.connect(self.download_clicked.emit)
        self.btn_delete.clicked.connect(self.delete_clicked.emit)
        self.btn_export.clicked.connect(self.export_clicked.emit)
