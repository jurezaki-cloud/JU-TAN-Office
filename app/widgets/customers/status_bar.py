from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget


class CustomerStatusBar(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("CustomerStatusBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 0)
        layout.setSpacing(16)

        self.count_label = QLabel("Stranke: 0")
        self.count_label.setObjectName("CustomerStatusLabel")

        self.selected_label = QLabel("Izbrana vrstica: ni izbrane")
        self.selected_label.setObjectName("CustomerStatusLabel")

        layout.addWidget(self.count_label)
        layout.addStretch()
        layout.addWidget(self.selected_label)

    def set_count(self, count: int) -> None:
        self.count_label.setText(f"Stranke: {count}")

    def set_selected(self, name: str | None) -> None:
        if name:
            self.selected_label.setText(f"Izbrana vrstica: {name}")
        else:
            self.selected_label.setText("Izbrana vrstica: ni izbrane")
