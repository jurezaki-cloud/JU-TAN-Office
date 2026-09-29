"""Slovenian texts for Qt's own UI strings (standard dialog buttons, edit context menus).

PySide6 ships no qtbase_sl.qm; without this, QMessageBox / QDialogButtonBox buttons and
text-field context menus appear in English inside the Slovenian UI.
"""

from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QTranslator

_EDIT_MENU = {
    "&Undo": "&Razveljavi",
    "&Redo": "&Uveljavi",
    "Cu&t": "Iz&reži",
    "&Copy": "&Kopiraj",
    "&Paste": "&Prilepi",
    "Delete": "Izbriši",
    "Select All": "Izberi vse",
}

_TEXTS: dict[str, dict[str, str]] = {
    "QPlatformTheme": {
        "OK": "V redu",
        "Save": "Shrani",
        "Save All": "Shrani vse",
        "Open": "Odpri",
        "&Yes": "&Da",
        "Yes to &All": "Da za &vse",
        "&No": "&Ne",
        "N&o to All": "N&e za vse",
        "Abort": "Prekini",
        "Retry": "Poskusi znova",
        "Ignore": "Prezri",
        "Close": "Zapri",
        "Cancel": "Prekliči",
        "Discard": "Zavrzi",
        "Help": "Pomoč",
        "Apply": "Uporabi",
        "Reset": "Ponastavi",
        "Restore Defaults": "Obnovi privzeto",
    },
    "QMessageBox": {
        "Show Details...": "Pokaži podrobnosti ...",
        "Hide Details...": "Skrij podrobnosti ...",
    },
    "QLineEdit": _EDIT_MENU,
    "QWidgetTextControl": {**_EDIT_MENU, "Copy &Link Location": "Kopiraj &naslov povezave"},
    "QAbstractSpinBox": {"&Select All": "&Izberi vse", "&Step up": "Korak &gor", "Step &down": "Korak &dol"},
}


class SlovenianQtTranslator(QTranslator):
    def translate(self, context, source_text, disambiguation=None, n=-1):
        # None is a null QString: Qt falls through to the source text. An empty
        # string would be taken as the translation and blank the label.
        return _TEXTS.get(context or "", {}).get(source_text)

    def isEmpty(self) -> bool:  # noqa: N802 — Qt API
        return False


def install_qt_translations(app: QCoreApplication) -> None:
    """Install once per application, before the first dialog is shown."""
    if getattr(app, "_jutan_qt_translator", None) is not None:
        return
    translator = SlovenianQtTranslator(app)
    app.installTranslator(translator)
    app._jutan_qt_translator = translator
