from PySide6.QtGui import QColor, QPalette


INK = "#0B1220"
NAVY = "#101A2E"
CYAN = "#19D3C5"
BLUE = "#3B82F6"
SURFACE = "#FFFFFF"
BACKGROUND = "#F3F6FA"
MUTED = "#64748B"


def apply_theme(app):
    palette = QPalette()

    palette.setColor(QPalette.Window, QColor(BACKGROUND))
    palette.setColor(QPalette.WindowText, QColor(INK))
    palette.setColor(QPalette.Base, QColor(SURFACE))
    palette.setColor(QPalette.AlternateBase, QColor("#F8FAFC"))
    palette.setColor(QPalette.Text, QColor(INK))
    palette.setColor(QPalette.Button, QColor(NAVY))
    palette.setColor(QPalette.ButtonText, QColor("#FFFFFF"))
    palette.setColor(QPalette.Highlight, QColor(CYAN))
    palette.setColor(QPalette.HighlightedText, QColor(INK))

    app.setPalette(palette)

    app.setStyleSheet("""
        QWidget {
            color: #0B1220;
            font-family: "Segoe UI", "Aptos", sans-serif;
            font-size:10pt;
        }
        QMainWindow, QStackedWidget { background: #F3F6FA; }
        QPushButton { background:#101A2E; color:white; border:1px solid #101A2E; border-radius:9px; padding:8px 15px; font-weight:600; }
        QPushButton:hover { background:#172844; border-color:#19D3C5; }
        QPushButton:pressed { background:#0B1220; }
        QPushButton:disabled { background:#CBD5E1; border-color:#CBD5E1; }
        QLineEdit,QComboBox,QTextEdit,QSpinBox,QDateEdit,QDoubleSpinBox { background:white; border:1px solid #D8E0EA; border-radius:8px; padding:7px 9px; selection-background-color:#19D3C5; }
        QLineEdit:focus,QComboBox:focus,QTextEdit:focus,QSpinBox:focus,QDateEdit:focus,QDoubleSpinBox:focus { border:1px solid #3B82F6; }
        QGroupBox { background:white; border:1px solid #E2E8F0; border-radius:13px; margin-top:14px; padding:18px 14px 14px 14px; font-weight:700; }
        QGroupBox::title { subcontrol-origin:margin; left:14px; padding:0 7px; }
        QTableView,QTableWidget,QListWidget { background:white; alternate-background-color:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px; gridline-color:#EDF2F7; selection-background-color:#D7F7F3; selection-color:#0B1220; }
        QHeaderView::section { background:#EAF0F6; color:#334155; border:none; border-bottom:1px solid #D8E0EA; padding:9px; font-weight:700; }
        QSplitter::handle { background:transparent; width:8px; }
        QScrollBar:vertical { background:transparent; width:10px; margin:2px; }
        QScrollBar::handle:vertical { background:#CBD5E1; border-radius:5px; min-height:24px; }
        QStatusBar { background:#FFFFFF; color:#64748B; border-top:1px solid #E2E8F0; }
        QToolTip { background:#101A2E; color:white; border:1px solid #19D3C5; padding:6px; }
    """)
