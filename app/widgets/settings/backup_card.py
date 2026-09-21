from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from app.widgets.cards.enterprise_card import EnterpriseCard


class BackupCard(QWidget):
    backup_requested = Signal()
    restore_requested = Signal()
    export_requested = Signal()
    import_requested = Signal()
    folder_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        card = EnterpriseCard("DashboardCard")
        title = QLabel("Backup Center")
        title.setObjectName("DashboardSectionTitle")
        caption = QLabel("Varnostne kopije baze in izvoz nastavitev")
        caption.setObjectName("DashboardMuted")
        card.body.addWidget(title)
        card.body.addWidget(caption)

        self.empty_hint = QLabel(
            "Če še nimate varnostne kopije, ustvarite prvo pred večjimi spremembami."
        )
        self.empty_hint.setObjectName("DashboardMuted")
        self.empty_hint.setWordWrap(True)
        card.body.addWidget(self.empty_hint)

        self.btn_backup = QPushButton("Backup Database")
        self.btn_backup.setObjectName("PrimaryButton")
        self.btn_restore = QPushButton("Restore Database")
        self.btn_restore.setObjectName("SecondaryButton")
        self.btn_export = QPushButton("Export Settings")
        self.btn_export.setObjectName("SecondaryButton")
        self.btn_import = QPushButton("Import Settings")
        self.btn_import.setObjectName("SecondaryButton")
        self.btn_folder = QPushButton("Open Backup Folder")
        self.btn_folder.setObjectName("SecondaryButton")

        for button, signal in (
            (self.btn_backup, self.backup_requested),
            (self.btn_restore, self.restore_requested),
            (self.btn_export, self.export_requested),
            (self.btn_import, self.import_requested),
            (self.btn_folder, self.folder_requested),
        ):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(36)
            card.body.addWidget(button)
            button.clicked.connect(signal.emit)

        layout.addWidget(card)
