from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from app.widgets.cards.enterprise_card import EnterpriseCard


class FollowupPanel(EnterpriseCard):

    def __init__(self, parent=None) -> None:
        super().__init__("DashboardCard", parent)
        self.setObjectName("FollowupPanel")

        title = QLabel("Follow up")
        title.setObjectName("SectionTitle")
        self.body.addWidget(title)

        self.lists = {}
        for key, caption in (
            ("today", "Today"),
            ("tomorrow", "Tomorrow"),
            ("week", "This Week"),
            ("overdue", "Overdue"),
        ):
            label = QLabel(caption)
            label.setObjectName("KpiTitle")
            widget = QListWidget()
            widget.setObjectName("EnterpriseTable")
            widget.setMaximumHeight(110)
            self.body.addWidget(label)
            self.body.addWidget(widget)
            self.lists[key] = widget

    def set_followups(self, buckets: dict) -> None:
        for key, widget in self.lists.items():
            widget.clear()
            for row in buckets.get(key) or []:
                widget.addItem(QListWidgetItem(
                    f"{row[4]} · {row[5] or '—'} · {str(row[6] or '')[:10]}"
                ))
