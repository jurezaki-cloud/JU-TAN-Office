from PySide6.QtWidgets import QLabel, QSizePolicy

from app.widgets.cards.enterprise_card import EnterpriseCard


class KpiCard(EnterpriseCard):

    def __init__(
        self,
        title: str,
        value: str = "0",
        hint: str = "",
        parent=None,
        *,
        tone: str | None = None,
    ):
        super().__init__("KpiCard", parent)

        self.setMinimumHeight(118)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        if tone:
            self.setProperty("tone", tone)

        self.caption = QLabel(title)
        self.caption.setObjectName("KpiTitle")

        self.value = QLabel(value)
        self.value.setObjectName("KpiValue")

        self.hint = QLabel(hint)
        self.hint.setObjectName("KpiHint")

        self.body.setSpacing(6)
        self.body.setContentsMargins(20, 18, 20, 18)
        self.body.addWidget(self.caption)
        self.body.addWidget(self.value)
        self.body.addWidget(self.hint)
        self.body.addStretch()

    def set_value(self, value: str, hint: str | None = None) -> None:
        self.value.setText(str(value))
        if hint is not None:
            self.hint.setText(hint)

    def set_tone(self, tone: str | None) -> None:
        self.setProperty("tone", tone or "")
        style = self.style()
        if style is not None:
            style.unpolish(self)
            style.polish(self)
        self.update()
