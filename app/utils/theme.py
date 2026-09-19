from PySide6.QtGui import QColor, QPalette


# JU-TAN Office design tokens
INK = "#0B1220"
NAVY = "#0F1B2D"
NAVY_HOVER = "#172A45"
NAVY_ACTIVE = "#123A4A"
CYAN = "#19D3C5"
CYAN_SOFT = "#D7F7F3"
BLUE = "#3B82F6"
SURFACE = "#FFFFFF"
BACKGROUND = "#F4F7FB"
SURFACE_ALT = "#F8FAFC"
BORDER = "#E2E8F0"
BORDER_STRONG = "#CBD5E1"
MUTED = "#64748B"
TEXT_SOFT = "#334155"
SUCCESS = "#16A34A"
WARNING = "#F59E0B"
DANGER = "#EF4444"

RADIUS_SM = 8
RADIUS_MD = 10
RADIUS_LG = 14


def apply_theme(app):
    """Apply the shared JU-TAN Office production theme."""
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(BACKGROUND))
    palette.setColor(QPalette.WindowText, QColor(INK))
    palette.setColor(QPalette.Base, QColor(SURFACE))
    palette.setColor(QPalette.AlternateBase, QColor(SURFACE_ALT))
    palette.setColor(QPalette.Text, QColor(INK))
    palette.setColor(QPalette.Button, QColor(NAVY))
    palette.setColor(QPalette.ButtonText, QColor("#FFFFFF"))
    palette.setColor(QPalette.Highlight, QColor(CYAN))
    palette.setColor(QPalette.HighlightedText, QColor(INK))
    palette.setColor(QPalette.PlaceholderText, QColor(MUTED))
    app.setPalette(palette)

    app.setStyleSheet("""
        QWidget {
            color: #0B1220;
            font-family: "Segoe UI", "Aptos", sans-serif;
            font-size: 10pt;
        }
        QMainWindow, QStackedWidget { background: #F4F7FB; }

        QLabel[role="pageTitle"] {
            font-size: 26px;
            font-weight: 700;
            color: #0B1220;
        }
        QLabel[role="pageSubtitle"] {
            color: #64748B;
            font-size: 10pt;
        }
        QLabel[role="muted"] { color: #64748B; }

        QPushButton {
            background: #0F1B2D;
            color: white;
            border: 1px solid #0F1B2D;
            border-radius: 9px;
            padding: 8px 15px;
            font-weight: 600;
            min-height: 18px;
        }
        QPushButton:hover { background: #172A45; border-color: #19D3C5; }
        QPushButton:pressed { background: #0B1220; }
        QPushButton:disabled {
            background: #E2E8F0;
            color: #94A3B8;
            border-color: #E2E8F0;
        }
        QPushButton[variant="secondary"] {
            background: white;
            color: #0F1B2D;
            border-color: #CBD5E1;
        }
        QPushButton[variant="secondary"]:hover {
            background: #F8FAFC;
            border-color: #19D3C5;
        }
        QPushButton[variant="danger"] {
            background: #EF4444;
            border-color: #EF4444;
        }

        QLineEdit, QComboBox, QTextEdit, QPlainTextEdit,
        QSpinBox, QDateEdit, QDoubleSpinBox {
            background: white;
            border: 1px solid #D8E0EA;
            border-radius: 8px;
            padding: 7px 9px;
            selection-background-color: #19D3C5;
            selection-color: #0B1220;
        }
        QLineEdit:focus, QComboBox:focus, QTextEdit:focus,
        QPlainTextEdit:focus, QSpinBox:focus, QDateEdit:focus,
        QDoubleSpinBox:focus { border: 1px solid #3B82F6; }

        QGroupBox {
            background: white;
            border: 1px solid #E2E8F0;
            border-radius: 13px;
            margin-top: 14px;
            padding: 18px 14px 14px 14px;
            font-weight: 700;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 14px;
            padding: 0 7px;
        }

        QTableView, QTableWidget, QListWidget {
            background: white;
            alternate-background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            gridline-color: #EDF2F7;
            selection-background-color: #D7F7F3;
            selection-color: #0B1220;
        }
        QHeaderView::section {
            background: #F1F5F9;
            color: #334155;
            border: none;
            border-bottom: 1px solid #D8E0EA;
            padding: 9px;
            font-weight: 700;
        }

        QTabWidget::pane {
            border: 1px solid #E2E8F0;
            background: white;
            border-radius: 10px;
        }
        QTabBar::tab {
            padding: 9px 14px;
            color: #64748B;
            font-weight: 600;
        }
        QTabBar::tab:selected { color: #0B1220; }

        QSplitter::handle { background: transparent; width: 8px; }
        QScrollBar:vertical {
            background: transparent;
            width: 10px;
            margin: 2px;
        }
        QScrollBar::handle:vertical {
            background: #CBD5E1;
            border-radius: 5px;
            min-height: 24px;
        }
        QStatusBar {
            background: #FFFFFF;
            color: #64748B;
            border-top: 1px solid #E2E8F0;
        }
        QToolTip {
            background: #0F1B2D;
            color: white;
            border: 1px solid #19D3C5;
            padding: 6px;
        }
    """)
