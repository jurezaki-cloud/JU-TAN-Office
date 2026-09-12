from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton

from app.core.ui.icons import apply_button_icon
from app.widgets.cards.enterprise_card import EnterpriseCard


class EmptyStateCard(EnterpriseCard):
    action_clicked = Signal()

    def __init__(self, title: str, subtitle: str, parent=None, action_text: str = "Dodaj prvi zapis"):
        super().__init__("EmptyStateCard", parent)

        self.setMinimumHeight(220)

        self.title = QLabel(title)
        self.title.setObjectName("EmptyStateTitle")
        self.title.setAlignment(Qt.AlignCenter)

        self.subtitle = QLabel(subtitle)
        self.subtitle.setObjectName("EmptyStateSubtitle")
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setWordWrap(True)

        self.action = QPushButton(action_text)
        self.action.setObjectName("PrimaryButton")
        self.action.setCursor(Qt.PointingHandCursor)
        self.action.setMinimumHeight(36)
        apply_button_icon(self.action, "new")
        self.action.clicked.connect(self.action_clicked.emit)

        self.body.addStretch()
        self.body.addWidget(self.title)
        self.body.addWidget(self.subtitle)
        self.body.addWidget(self.action, 0, Qt.AlignHCenter)
        self.body.addStretch()

    def set_message(self, title: str, subtitle: str, show_action: bool | None = None) -> None:
        self.title.setText(title)
        self.subtitle.setText(subtitle)
        if show_action is None:
            show_action = "zadetkov" not in (title or "").casefold()
        self.action.setVisible(show_action)
