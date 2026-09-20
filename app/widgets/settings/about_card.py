from PySide6.QtWidgets import QFormLayout, QLabel, QVBoxLayout, QWidget

from app.widgets.cards.enterprise_card import EnterpriseCard


class AboutCard(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        card = EnterpriseCard("DashboardCard")
        title = QLabel("About")
        title.setObjectName("DashboardSectionTitle")
        card.body.addWidget(title)

        self.app_name = QLabel("JU-TAN Office")
        self.app_name.setObjectName("DashboardWelcome")
        self.edition = QLabel("Enterprise Edition")
        self.edition.setObjectName("DashboardMuted")
        card.body.addWidget(self.app_name)
        card.body.addWidget(self.edition)

        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(8)

        self.lbl_version = QLabel("-")
        self.lbl_python = QLabel("-")
        self.lbl_qt = QLabel("-")
        self.lbl_sqlite = QLabel("-")
        self.lbl_build = QLabel("-")
        self.lbl_copy = QLabel("-")

        for label in (
            self.lbl_version,
            self.lbl_python,
            self.lbl_qt,
            self.lbl_sqlite,
            self.lbl_build,
            self.lbl_copy,
        ):
            label.setObjectName("DetailValue")

        form.addRow("Version", self.lbl_version)
        form.addRow("Python Version", self.lbl_python)
        form.addRow("Qt Version", self.lbl_qt)
        form.addRow("SQLite Version", self.lbl_sqlite)
        form.addRow("Build Date", self.lbl_build)
        form.addRow("Copyright", self.lbl_copy)
        card.body.addLayout(form)
        layout.addWidget(card)

    def set_values(self, info: dict) -> None:
        self.app_name.setText(info.get("app", "JU-TAN Office"))
        self.edition.setText(info.get("edition", "Enterprise Edition"))
        self.lbl_version.setText(info.get("version", "-"))
        self.lbl_python.setText(info.get("python", "-"))
        self.lbl_qt.setText(info.get("qt", "-"))
        self.lbl_sqlite.setText(info.get("sqlite", "-"))
        self.lbl_build.setText(info.get("build", "-"))
        self.lbl_copy.setText(info.get("copyright", "-"))
