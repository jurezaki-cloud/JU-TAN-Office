from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QSizePolicy,
    QVBoxLayout,
)


class EnterpriseCard(QFrame):
    """Surface card with QSS elevation only — no QGraphicsDropShadowEffect.

    Graphics effects force off-screen buffers and cause temporary frame outlines
    when navigating stacked pages or hovering many cards.
    """

    def __init__(self, object_name: str = "DashboardCard", parent=None):
        super().__init__(parent)

        self.setObjectName(object_name)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(20, 20, 20, 20)
        self.body.setSpacing(12)
