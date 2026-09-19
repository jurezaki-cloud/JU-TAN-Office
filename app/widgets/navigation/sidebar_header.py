from __future__ import annotations



import weakref

from pathlib import Path



from PySide6.QtCore import Qt

from PySide6.QtGui import QPixmap

from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout, QWidget



from app.core.constants import BASE_DIR, DATA_DIR, RESOURCE_DIR

from app.theme.colors import ThemeMode





_instances: weakref.WeakSet["SidebarHeader"] = weakref.WeakSet()





def resolve_brand_logo(mode: ThemeMode | None = None) -> Path | None:

    """Return the theme-appropriate brand logo path (application UI only).



    LIGHT prefers logo_light.png; DARK prefers logo_dark.png.

    logo.png remains a universal fallback. First existing valid file wins.

    """

    from app.theme.theme import theme_manager



    active = mode if mode is not None else theme_manager.mode

    themed = "logo_dark.png" if active == ThemeMode.DARK else "logo_light.png"

    fallback = "logo.png"

    candidates = (

        DATA_DIR / themed,

        DATA_DIR / fallback,

        BASE_DIR / "data" / themed,

        BASE_DIR / "data" / fallback,

        RESOURCE_DIR / themed,

        RESOURCE_DIR / fallback,

        BASE_DIR / "resources" / themed,

        BASE_DIR / "resources" / fallback,

    )

    for path in candidates:

        if path.is_file():

            return path

    return None





def refresh_brand_logos() -> None:

    """Reload logos on all live SidebarHeader instances after a theme change."""

    for header in list(_instances):

        header.refresh_logo()





class SidebarHeader(QWidget):



    def __init__(self, parent=None):

        super().__init__(parent)



        self.setObjectName("SidebarHeader")

        self.setAttribute(Qt.WA_StyledBackground, True)

        self._collapsed = False



        layout = QVBoxLayout(self)

        layout.setContentsMargins(4, 4, 4, 8)

        layout.setSpacing(8)



        self.logo = QLabel()

        self.logo.setObjectName("SidebarLogo")

        self.logo.setAlignment(Qt.AlignCenter)

        self.logo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.logo.setMinimumHeight(40)

        self.logo.setMaximumHeight(72)

        layout.addWidget(self.logo)



        self.brand = QLabel("JU-TAN")

        self.brand.setObjectName("SidebarBrand")

        self.brand.setAlignment(Qt.AlignCenter)

        self.brand.hide()

        layout.addWidget(self.brand)



        line = QFrame()

        line.setObjectName("SidebarHeaderLine")

        line.setFrameShape(QFrame.HLine)

        line.setFixedHeight(1)

        layout.addWidget(line)



        self._logo_path: Path | None = None

        _instances.add(self)

        self._load_logo()



    def set_collapsed(self, collapsed: bool) -> None:

        self._collapsed = bool(collapsed)

        if self._collapsed:

            self.logo.hide()

            self.brand.show()

            self.brand.setText("JT")

            self.setMaximumHeight(56)

        else:

            self.brand.hide()

            self.logo.show()

            self.setMaximumHeight(16777215)

            self._logo_path = None

            self._load_logo()



    def refresh_logo(self) -> None:

        """Force reload so LIGHT/DARK logo swaps take effect immediately."""

        self._logo_path = None

        self._load_logo()



    def _load_logo(self) -> None:

        if self._collapsed:

            return

        path = resolve_brand_logo()

        if path is None:

            self.logo.hide()

            self.brand.show()

            self.brand.setText("JU-TAN")

            return



        if path == self._logo_path and self.logo.pixmap() is not None and not self.logo.pixmap().isNull():

            return



        pixmap = QPixmap(str(path))

        if pixmap.isNull():

            self.logo.hide()

            self.brand.show()

            self.brand.setText("JU-TAN")

            return



        ratio = max(1.0, float(self.devicePixelRatioF() or 1.0))

        target_w = int(180 * ratio)

        target_h = int(56 * ratio)

        scaled = pixmap.scaled(

            target_w,

            target_h,

            Qt.KeepAspectRatio,

            Qt.SmoothTransformation,

        )

        scaled.setDevicePixelRatio(ratio)

        self.logo.setPixmap(scaled)

        self.logo.setText("")

        self.logo.show()

        self.brand.hide()

        self._logo_path = path

        self.logo.setFixedHeight(int(scaled.height() / ratio) + 4)



    def showEvent(self, event):

        super().showEvent(event)

        if not self._collapsed:

            self._logo_path = None

            self._load_logo()


