from PySide6.QtWidgets import QLabel

from app.modules.warehouse.warehouse_service import StockRow
from app.widgets.cards.enterprise_card import EnterpriseCard


class StockCard(EnterpriseCard):

    def __init__(self, parent=None) -> None:
        super().__init__("KpiCard", parent)

        self.setMinimumHeight(220)

        self.caption = QLabel("Izbrani artikel")
        self.caption.setObjectName("KpiTitle")

        self.value = QLabel("—")
        self.value.setObjectName("KpiValue")

        self.hint = QLabel("Izberi vrstico v tabeli zaloge")
        self.hint.setObjectName("KpiHint")
        self.hint.setWordWrap(True)

        self.status = QLabel("")
        self.status.setObjectName("KpiHint")

        self.body.setSpacing(6)
        self.body.addWidget(self.caption)
        self.body.addWidget(self.value)
        self.body.addWidget(self.hint)
        self.body.addWidget(self.status)
        self.body.addStretch()

    def load(self, row: StockRow | None) -> None:
        if row is None:
            self.value.setText("—")
            self.hint.setText("Izberi vrstico v tabeli zaloge")
            self.status.setText("")
            return
        self.value.setText(row.name or row.code or "—")
        self.hint.setText(
            f"{row.code or '—'} · {row.warehouse}\n"
            f"Na zalogi {_fmt(row.qty)} · Rezervirano {_fmt(row.reserved)} · "
            f"Prosto {_fmt(row.free)}"
        )
        self.status.setText(f"{row.status} · min. {_fmt(row.min_qty)}")


def _fmt(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}".replace(".", ",")
