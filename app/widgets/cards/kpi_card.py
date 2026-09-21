from PySide6.QtWidgets import QLabel, QSizePolicy

from app.theme.tokens import SPACE_2, SPACE_4, SPACE_5
from app.widgets.cards.enterprise_card import EnterpriseCard


class KpiCard(EnterpriseCard):
    """Metric tile. Use tone='primary' + dominant=True for the hero business KPI."""

    def __init__(
        self,
        title: str,
        value: str = "0",
        hint: str = "",
        parent=None,
        *,
        tone: str | None = None,
        dominant: bool = False,
    ):
        super().__init__("KpiCard", parent)

        self._dominant = dominant
        self.setMinimumHeight(136 if dominant else 118)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        if tone:
            self.setProperty("tone", tone)
        if dominant:
            self.setProperty("prominence", "dominant")

        self.caption = QLabel(title)
        self.caption.setObjectName("KpiTitle")

        self.value = QLabel(value)
        self.value.setObjectName("KpiValue")

        self.hint = QLabel(hint)
        self.hint.setObjectName("KpiHint")

        if dominant:
            self.body.setSpacing(SPACE_2)
            self.body.setContentsMargins(SPACE_5, SPACE_4, SPACE_5, SPACE_4)
        else:
            self.body.setSpacing(6)
            self.body.setContentsMargins(SPACE_5, 18, SPACE_5, 18)
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
