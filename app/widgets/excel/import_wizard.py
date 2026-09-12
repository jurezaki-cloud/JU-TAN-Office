from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.excel.excel_export import analyze_file, excel_folders, map_rows
from app.excel.excel_import import existing_keys, export_template, run_import
from app.excel.excel_mapping import MODULES, suggest_mapping
from app.excel.excel_validation import validate_rows
from app.widgets.cards.enterprise_card import EnterpriseCard


class ExcelImportWizard(EnterpriseDialog):

    def __init__(self, parent=None, module: str = "customers"):
        super().__init__(
            parent,
            title="Excel uvoz",
            heading="1. Izberi Excel datoteko",
            size="MEDIUM",
            state_key="dialog.excel",
            show_footer=True,
        )
        self.module = module if module in MODULES else "customers"
        self.analysis = None
        self.summary = None
        self.setObjectName("ExcelWizard")
        self.btn_save.hide()
        self.btn_cancel.hide()
        self.title = self.heading

        self.stack = QStackedWidget()
        self.stack.addWidget(self._step_file())
        self.stack.addWidget(self._step_analysis())
        self.stack.addWidget(self._step_mapping())
        self.stack.addWidget(self._step_validation())
        self.stack.addWidget(self._step_summary())
        self.body.addWidget(self.stack)

        self.btn_back = QPushButton("Nazaj")
        self.btn_back.setObjectName("SecondaryButton")
        self.btn_next = QPushButton("Naprej")
        self.btn_next.setObjectName("PrimaryButton")
        self.btn_close = QPushButton("Zapri")
        self.btn_close.setObjectName("SecondaryButton")
        for button in (self.btn_back, self.btn_close, self.btn_next):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(36)
        self.footer_layout.insertWidget(0, self.btn_back)
        self.footer_layout.addWidget(self.btn_close)
        self.footer_layout.addWidget(self.btn_next)

        self.btn_close.clicked.connect(self.accept)
        self.btn_back.clicked.connect(self._back)
        self.btn_next.clicked.connect(self._next)
        self.btn_back.setEnabled(False)
        self._update_title()

    def _step_file(self) -> QWidget:
        card = EnterpriseCard("DashboardCard")
        caption = QLabel(f"Modul: {MODULES[self.module]['title']}")
        caption.setObjectName("DashboardMuted")
        card.body.addWidget(caption)
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        pick = QPushButton("Izberi Excel datoteko")
        pick.setObjectName("SecondaryButton")
        pick.setMinimumHeight(36)
        pick.setCursor(Qt.PointingHandCursor)
        pick.clicked.connect(self._pick_file)
        template = QPushButton("Export Template")
        template.setObjectName("SecondaryButton")
        template.setMinimumHeight(36)
        template.setCursor(Qt.PointingHandCursor)
        template.clicked.connect(self._save_template)
        row = QHBoxLayout()
        row.addWidget(self.file_path, 1)
        row.addWidget(pick)
        card.body.addLayout(row)
        card.body.addWidget(template)
        return card

    def _step_analysis(self) -> QWidget:
        card = EnterpriseCard("DashboardCard")
        self.analysis_label = QLabel("Datoteka še ni analizirana.")
        self.analysis_label.setObjectName("DetailValue")
        self.analysis_label.setWordWrap(True)
        self.headers_list = QListWidget()
        card.body.addWidget(self.analysis_label)
        card.body.addWidget(self.headers_list)
        return card

    def _step_mapping(self) -> QWidget:
        card = EnterpriseCard("DashboardCard")
        hint = QLabel("Preslikaj stolpce iz Excela na polja JU-TAN Office.")
        hint.setObjectName("DashboardMuted")
        card.body.addWidget(hint)
        self.mapping_form = QFormLayout()
        self.mapping_form.setHorizontalSpacing(16)
        self.mapping_form.setVerticalSpacing(8)
        self.mapping_combos: dict[str, QComboBox] = {}
        card.body.addLayout(self.mapping_form)
        return card

    def _step_validation(self) -> QWidget:
        card = EnterpriseCard("DashboardCard")
        self.validation_view = QTextEdit()
        self.validation_view.setReadOnly(True)
        card.body.addWidget(self.validation_view)
        return card

    def _step_summary(self) -> QWidget:
        card = EnterpriseCard("DashboardCard")
        self.lbl_imported = QLabel("Imported: 0")
        self.lbl_skipped = QLabel("Skipped: 0")
        self.lbl_warnings = QLabel("Warnings: 0")
        self.lbl_errors = QLabel("Errors: 0")
        for label in (
            self.lbl_imported,
            self.lbl_skipped,
            self.lbl_warnings,
            self.lbl_errors,
        ):
            label.setObjectName("KpiValue")
            card.body.addWidget(label)
        self.summary_view = QTextEdit()
        self.summary_view.setReadOnly(True)
        card.body.addWidget(self.summary_view)
        return card

    def _pick_file(self):
        start = str(excel_folders()["import"])
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Izberi Excel datoteko",
            start,
            "Excel (*.xlsx *.xlsm)",
        )
        if path:
            self.file_path.setText(path)

    def _save_template(self):
        start = str(excel_folders()["export"] / f"{self.module}_template.xlsx")
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Template",
            start,
            "Excel (*.xlsx)",
        )
        if path:
            export_template(self.module, Path(path))

    def _update_title(self):
        titles = [
            "1. Izberi Excel datoteko",
            "2. Analiza strukture",
            "3. Preslikava stolpcev",
            "4. Validacija podatkov",
            "5. Povzetek in potrditev",
        ]
        self.title.setText(titles[self.stack.currentIndex()])
        self.btn_back.setEnabled(self.stack.currentIndex() > 0)
        last = self.stack.currentIndex() == 4
        self.btn_next.setText("Uvozi" if last else "Naprej")

    def _back(self):
        index = self.stack.currentIndex()
        if index > 0:
            self.stack.setCurrentIndex(index - 1)
            self.btn_next.setEnabled(True)
            self._update_title()

    def _next(self):
        step = self.stack.currentIndex()
        if step == 0:
            if not self.file_path.text().strip():
                return
            self._fill_analysis()
            self.stack.setCurrentIndex(1)
        elif step == 1:
            self._fill_mapping()
            self.stack.setCurrentIndex(2)
        elif step == 2:
            self._fill_validation()
            self.stack.setCurrentIndex(3)
        elif step == 3:
            self.stack.setCurrentIndex(4)
            self._reset_summary()
        elif step == 4:
            self._run_import()
        self._update_title()

    def _fill_analysis(self):
        self.analysis = analyze_file(Path(self.file_path.text()))
        self.analysis_label.setText(
            f"List: {self.analysis['sheet']}\n"
            f"Vrstice: {self.analysis['count']}\n"
            f"Glava v vrstici {self.analysis['header_row']}"
        )
        self.headers_list.clear()
        self.headers_list.addItems([h for h in self.analysis["headers"] if h])

    def _fill_mapping(self):
        suggested = suggest_mapping(self.analysis["headers"], self.module)
        while self.mapping_form.rowCount():
            self.mapping_form.removeRow(0)
        self.mapping_combos.clear()
        for spec in MODULES[self.module]["fields"]:
            combo = QComboBox()
            combo.setObjectName("EnterpriseFilter")
            combo.setMinimumHeight(36)
            combo.addItem("(preskoči)", "")
            for header in [h for h in self.analysis["headers"] if h]:
                combo.addItem(header, header)
            wanted = suggested.get(spec.key, "")
            index = combo.findData(wanted)
            if index >= 0:
                combo.setCurrentIndex(index)
            self.mapping_combos[spec.key] = combo
            label = spec.label + (" *" if spec.required else "")
            self.mapping_form.addRow(label, combo)

    def mapping(self) -> dict[str, str]:
        return {
            key: combo.currentData() or ""
            for key, combo in self.mapping_combos.items()
        }

    def _fill_validation(self):
        mapped = map_rows(self.analysis, self.mapping())
        _, issues = validate_rows(self.module, mapped, existing_keys(self.module))
        if not issues:
            self.validation_view.setPlainText("Validacija je uspešna. Ni napak.")
            return
        lines = [f"Vrstica {item.row} · {item.level} · {item.message}" for item in issues]
        self.validation_view.setPlainText("\n".join(lines))

    def _reset_summary(self):
        self.lbl_imported.setText("Imported: 0")
        self.lbl_skipped.setText("Skipped: 0")
        self.lbl_warnings.setText("Warnings: 0")
        self.lbl_errors.setText("Errors: 0")
        self.summary_view.setPlainText(
            "Pritisni Uvozi za potrditev. Posamezne napake ne prekinejo uvoza."
        )

    def _run_import(self):
        if not self.file_path.text():
            return
        self.summary = run_import(
            self.module,
            Path(self.file_path.text()),
            self.mapping(),
        )
        self.lbl_imported.setText(f"Imported: {self.summary.imported}")
        self.lbl_skipped.setText(f"Skipped: {self.summary.skipped}")
        self.lbl_warnings.setText(f"Warnings: {self.summary.warnings}")
        self.lbl_errors.setText(f"Errors: {self.summary.errors}")
        self.summary_view.setPlainText(
            "\n".join(self.summary.messages) or "Uvoz končan."
        )
        self.btn_next.setEnabled(False)


def run_excel_export(parent, module: str) -> None:
    from PySide6.QtWidgets import QFileDialog

    from app.excel.excel_import import export_module

    start = str(excel_folders()["export"] / f"{module}.xlsx")
    path, _ = QFileDialog.getSaveFileName(
        parent,
        "Excel izvoz",
        start,
        "Excel (*.xlsx)",
    )
    if not path:
        return
    from app.core.ui.busy import run_busy
    from app.core.ui.notify import toast

    run_busy(parent, "Izvoz Excel…", lambda: export_module(module, Path(path)))
    toast(parent, "Excel izvožen")


def run_excel_import(parent, module: str, on_done=None) -> None:
    wizard = ExcelImportWizard(parent, module)
    wizard.exec()
    if on_done:
        on_done()
