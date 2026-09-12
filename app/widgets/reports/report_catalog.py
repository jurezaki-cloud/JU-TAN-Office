from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem


class ReportCatalog(QListWidget):
    report_chosen = Signal(str)

    def __init__(self, catalog, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("EnterpriseTable")
        self.setMinimumWidth(200)
        for group, reports in catalog:
            header = QListWidgetItem(group)
            header.setFlags(Qt.NoItemFlags)
            header.setData(Qt.UserRole, "")
            self.addItem(header)
            for key, title in reports:
                item = QListWidgetItem("  " + title)
                item.setData(Qt.UserRole, key)
                self.addItem(item)
        self.currentItemChanged.connect(self._changed)

    def _changed(self, current, _previous) -> None:
        if current is None:
            return
        key = current.data(Qt.UserRole)
        if key:
            self.report_chosen.emit(str(key))
