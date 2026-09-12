from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem

from app.widgets.cards.enterprise_card import EnterpriseCard


class ActivityPanel(EnterpriseCard):

    def __init__(self, parent=None) -> None:
        super().__init__("DashboardCard", parent)
        self.setObjectName("ActivityPanel")

        title = QLabel("Aktivnosti")
        title.setObjectName("SectionTitle")
        self.body.addWidget(title)

        self.list = QListWidget()
        self.list.setObjectName("EnterpriseTable")
        self.body.addWidget(self.list, 1)

    def set_activities(self, rows: list) -> None:
        self.list.clear()
        for row in rows:
            item = QListWidgetItem(
                f"{row[4]} · {row[5] or '—'} · {str(row[6] or '')[:10]} · {row[7] or ''}"
            )
            item.setData(256, int(row[0]))
            self.list.addItem(item)
