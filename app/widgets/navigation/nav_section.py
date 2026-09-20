"""Navigation section label for grouped sidebar."""



from PySide6.QtCore import Qt

from PySide6.QtWidgets import QLabel, QSizePolicy



from app.theme.tokens import NAV_SECTION_HEIGHT





class NavSectionLabel(QLabel):

    def __init__(self, text: str, parent=None):

        super().__init__(text, parent)

        self.setObjectName("NavSectionLabel")

        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.setFixedHeight(NAV_SECTION_HEIGHT)


