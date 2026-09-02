from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt


PRIMARY = "#1F2937"
ACCENT = "#C8A24A"
BACKGROUND = "#F8F9FA"
WHITE = "#FFFFFF"


def apply_theme(app):
    palette = QPalette()

    palette.setColor(QPalette.Window, QColor(BACKGROUND))
    palette.setColor(QPalette.WindowText, Qt.black)

    palette.setColor(QPalette.Base, QColor(WHITE))
    palette.setColor(QPalette.AlternateBase, QColor(BACKGROUND))

    palette.setColor(QPalette.Button, QColor(PRIMARY))
    palette.setColor(QPalette.ButtonText, Qt.white)

    palette.setColor(QPalette.Highlight, QColor(ACCENT))
    palette.setColor(QPalette.HighlightedText, Qt.black)

    app.setPalette(palette)

    app.setStyleSheet("""
        QWidget{
            font-family:Aptos;
            font-size:10pt;
        }

        QPushButton{
            background:#1F2937;
            color:white;
            border:none;
            border-radius:8px;
            padding:8px 16px;
        }

        QPushButton:hover{
            background:#374151;
        }

        QLineEdit,QComboBox,QTextEdit{
            border:1px solid #D6D6D6;
            border-radius:8px;
            padding:6px;
            background:white;
        }

        QTableWidget{
            gridline-color:#E5E7EB;
            selection-background-color:#C8A24A;
        }
    """)