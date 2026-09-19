from PySide6.QtCore import Qt, Signal

from PySide6.QtWidgets import QFrame, QScrollArea, QVBoxLayout, QWidget



from app.core.ui.brand_icons import NAV_ICONS, brand_icon

from app.theme.colors import semantic_color

from app.theme.tokens import SIDEBAR_WIDTH, SIDEBAR_WIDTH_COLLAPSED, SPACE_1, SPACE_2

from app.widgets.navigation.nav_section import NavSectionLabel

from app.widgets.navigation.navigation import NAV_GROUPS

from app.widgets.navigation.navigation_button import NavigationButton

from app.widgets.navigation.sidebar_footer import SidebarFooter

from app.widgets.navigation.sidebar_header import SidebarHeader





class ModernSidebar(QWidget):



    page_changed = Signal(int)

    collapsed_changed = Signal(bool)



    def __init__(self, parent=None):

        super().__init__(parent)



        self.setObjectName("Sidebar")

        self.setAttribute(Qt.WA_StyledBackground, True)

        self.setFixedWidth(SIDEBAR_WIDTH)

        self._collapsed = False



        layout = QVBoxLayout(self)

        layout.setContentsMargins(10, 10, 8, 10)

        layout.setSpacing(SPACE_1)



        self.header = SidebarHeader()

        layout.addWidget(self.header)



        nav = QWidget()

        nav.setObjectName("SidebarNav")

        self._nav_layout = QVBoxLayout(nav)

        self._nav_layout.setContentsMargins(0, 2, 2, 2)

        self._nav_layout.setSpacing(1)



        self.buttons: dict[int, NavigationButton] = {}

        self._section_labels: list[NavSectionLabel] = []



        icon_color = semantic_color("SIDEBAR_TEXT", "#F8FAFC")

        for section_title, pages in NAV_GROUPS:

            label = NavSectionLabel(section_title)

            self._nav_layout.addWidget(label)

            self._section_labels.append(label)

            for text, index in pages:

                icon_name = NAV_ICONS.get(index, "documents")

                button = NavigationButton(

                    text,

                    index,

                    icon=brand_icon(icon_name, color=icon_color, size=18),

                )

                button.set_icon_name(icon_name)

                button.clicked_index.connect(self._on_navigate)

                self._nav_layout.addWidget(button)

                self.buttons[index] = button



        self._nav_layout.addStretch(1)



        self._nav_scroll = QScrollArea()

        self._nav_scroll.setObjectName("SidebarNavScroll")

        self._nav_scroll.setWidgetResizable(True)

        self._nav_scroll.setFrameShape(QFrame.NoFrame)

        self._nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._nav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self._nav_scroll.setFocusPolicy(Qt.StrongFocus)

        self._nav_scroll.setWidget(nav)

        # Smooth wheel / touchpad scrolling

        self._nav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)



        layout.addWidget(self._nav_scroll, 1)



        self.footer = SidebarFooter()

        self.footer.collapse_toggled.connect(self.set_collapsed)

        layout.addWidget(self.footer)



        self.set_active(0)



    def apply_role(self) -> None:

        from app.core.permissions import can_open_page



        for index, button in self.buttons.items():

            button.setVisible(can_open_page(index))

        self._refresh_section_visibility()

        self.footer.refresh()



    def _refresh_section_visibility(self) -> None:

        """Hide section labels when every item in the group is hidden (RBAC)."""

        from app.core.permissions import can_open_page



        idx = 0

        for section_title, pages in NAV_GROUPS:

            if idx >= len(self._section_labels):

                break

            visible = any(can_open_page(i) for _, i in pages)

            self._section_labels[idx].setVisible(visible and not self._collapsed)

            idx += 1



    def set_collapsed(self, collapsed: bool) -> None:

        self._collapsed = bool(collapsed)

        width = SIDEBAR_WIDTH_COLLAPSED if self._collapsed else SIDEBAR_WIDTH

        self.setFixedWidth(width)

        # Drive QSS so collapsed selected weight matches expanded (not stronger).
        self.setProperty("collapsed", "true" if self._collapsed else "false")
        self.style().unpolish(self)
        self.style().polish(self)

        self.header.set_collapsed(self._collapsed)

        self.footer.set_collapsed(self._collapsed)

        for button in self.buttons.values():

            button.set_collapsed(self._collapsed)

            button.refresh_active_icon()

        self._refresh_section_visibility()

        self.collapsed_changed.emit(self._collapsed)



    def _on_navigate(self, index: int):

        self.set_active(index)

        self.page_changed.emit(index)



    def set_active(self, index: int):

        for button_index, button in self.buttons.items():

            button.blockSignals(True)

            button.setChecked(button_index == index)

            button.blockSignals(False)

            button.refresh_active_icon()

        active = self.buttons.get(index)

        if active is not None and hasattr(self, "_nav_scroll"):

            self._nav_scroll.ensureWidgetVisible(active, 0, 20)



    def refresh_icons(self) -> None:

        for index, button in self.buttons.items():

            name = NAV_ICONS.get(index, "documents")

            button.set_icon_name(name)

            button.refresh_active_icon()

        self.footer._refresh_collapse_icon()



    def keyPressEvent(self, event):

        """Arrow-key navigation across visible nav buttons."""

        key = event.key()

        if key not in (Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp, Qt.Key_PageDown, Qt.Key_Home, Qt.Key_End):

            return super().keyPressEvent(event)



        visible = [b for b in self.buttons.values() if not b.isHidden()]

        if not visible:

            return

        current = next((i for i, b in enumerate(visible) if b.isChecked()), 0)

        if key == Qt.Key_Up:

            current = max(0, current - 1)

        elif key == Qt.Key_Down:

            current = min(len(visible) - 1, current + 1)

        elif key == Qt.Key_PageUp:

            current = max(0, current - 5)

        elif key == Qt.Key_PageDown:

            current = min(len(visible) - 1, current + 5)

        elif key == Qt.Key_Home:

            current = 0

        elif key == Qt.Key_End:

            current = len(visible) - 1

        target = visible[current]

        self.set_active(target.index)

        self.page_changed.emit(target.index)


