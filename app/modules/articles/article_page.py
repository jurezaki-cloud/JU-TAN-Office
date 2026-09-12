from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QMessageBox,
    QStackedWidget,
)

from app.modules.articles.models.article_table_model import ArticleTableModel
from app.modules.articles.article_dialog import ArticleDialog
from app.modules.articles.article_details import ArticleDetails
from app.database.article_repository import article_repository
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.customers.empty_state import EmptyStateCard
from app.widgets.invoices.status_badge import StatusBadgeDelegate
from app.widgets.articles.article_actions import ArticleActions
from app.widgets.articles.article_table import ArticleTable
from app.widgets.articles.search_field import ArticleSearch
from app.widgets.articles.status_bar import ArticleStatusBar
from app.widgets.excel.import_wizard import run_excel_export, run_excel_import


class ArticlePage(QWidget):

    def __init__(self):
        super().__init__()

        self.setObjectName("ArticlePage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title = QLabel("Artikli")
        title.setObjectName("PageTitle")
        title.hide()
        layout.addWidget(title)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)

        self.actions = ArticleActions()
        self.btn_new = self.actions.btn_new
        self.btn_edit = self.actions.btn_edit
        self.btn_delete = self.actions.btn_delete
        self.btn_refresh = self.actions.btn_refresh

        self.search_field = ArticleSearch()
        self.search = self.search_field.input

        top_layout.addWidget(self.actions)
        top_layout.addStretch()
        top_layout.addWidget(self.search_field)
        layout.addLayout(top_layout)

        self.table = ArticleTable()
        self.model = ArticleTableModel([])
        self.table.setModel(self.model)
        self.table.setColumnHidden(0, True)
        self.table.setItemDelegateForColumn(5, StatusBadgeDelegate(self.table))

        self.details = ArticleDetails()

        table_card = EnterpriseCard("DashboardCard")
        table_card.body.setContentsMargins(8, 8, 8, 8)
        table_card.body.addWidget(self.table)

        splitter = QSplitter()
        splitter.setObjectName("ArticleSplitter")
        splitter.addWidget(table_card)
        splitter.addWidget(self.details)
        splitter.setSizes([720, 360])
        splitter.setChildrenCollapsible(False)

        self.empty_state = EmptyStateCard(
            "Ni artiklov",
            "Dodajte prvi artikel v katalog.",
        )
        self.empty_state.action_clicked.connect(self.new_article)

        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self.empty_state)
        self.content_stack.addWidget(splitter)
        layout.addWidget(self.content_stack, 1)

        self.status = ArticleStatusBar()
        layout.addWidget(self.status)

        from app.core.pagination import IncrementalLoader
        from app.core.ui.debounce import Debouncer
        self._loader = IncrementalLoader(
            lambda offset, size: article_repository.list_page(
                self.search.text().strip(), limit=size, offset=offset
            )
        )
        self._search_debounced = Debouncer(self.search_article, 180, self)
        self.search.textChanged.connect(self._search_debounced)
        self.btn_new.clicked.connect(self.new_article)
        self.btn_edit.clicked.connect(self.edit_selected_article)
        self.btn_delete.clicked.connect(self.delete_article)
        self.btn_refresh.clicked.connect(self.refresh)
        self.actions.excel_clicked.connect(lambda: run_excel_export(self, "products"))
        self.actions.import_clicked.connect(
            lambda: run_excel_import(self, "products", self.refresh)
        )
        self.actions.filter_changed.connect(self._apply_view)

        self.table.clicked.connect(self.show_details)
        self.table.doubleClicked.connect(self.edit_article)
        self.details.editButton.clicked.connect(
            self.edit_selected_article
        )
        self.table.selectionModel().selectionChanged.connect(
            self._update_status
        )

        from app.core.ui.window_state import remember_layout
        remember_layout(self, "page.articles", splitters=[splitter], tables=[self.table], fields=[self.search, self.actions.filter])
        self.table.verticalScrollBar().valueChanged.connect(self._maybe_more)
        self.refresh()

    def refresh(self):
        self._apply_view()

    def search_article(self, text):
        self._apply_view()

    def new_article(self):
        dialog = ArticleDialog(self)

        if dialog.exec():

            data = dialog.get_data()

            if not data["name"]:
                return

            article_repository.add(
                data["code"],
                data["name"],
                data["description"],
                data["unit"],
                data["price"],
                data["vat"],
            )

            self.refresh()

    def show_details(self, index):
        row = index.row()

        article_id = self.model.articles[row][0]

        article = article_repository.get_by_id(article_id)

        if article:
            self.details.load_article(article)
        self._update_status()

    def edit_selected_article(self):

        if self.details.article_id is None:
            article = self.current_article()
            if article:
                self.edit_article_by_data(article)
                return
            QMessageBox.information(
                self,
                "Artikli",
                "Najprej izberi artikel.",
            )
            return

        article = article_repository.get_by_id(
            self.details.article_id
        )

        if article:
            self.edit_article_by_data(article)

    def edit_article(self, index):

        row = index.row()

        article_id = self.model.articles[row][0]

        article = article_repository.get_by_id(article_id)

        if article:
            self.edit_article_by_data(article)

    def edit_article_by_data(self, article):

        article_dict = {
            "id": article[0],
            "code": article[1],
            "name": article[2],
            "description": article[3],
            "unit": article[4],
            "price": article[5],
            "vat": article[6],
        }

        dialog = ArticleDialog(self, article_dict)

        if dialog.exec():

            data = dialog.get_data()

            article_repository.update(
                article[0],
                data["code"],
                data["name"],
                data["description"],
                data["unit"],
                data["price"],
                data["vat"],
            )

            self.refresh()

            updated = article_repository.get_by_id(article[0])

            if updated:
                self.details.load_article(updated)

    def delete_article(self):
        article_id = self.details.article_id
        if article_id is None:
            selected = self.current_article()
            if selected is None:
                QMessageBox.information(
                    self,
                    "Artikli",
                    "Najprej izberi artikel.",
                )
                return
            article_id = selected[0]

        article = article_repository.get_by_id(article_id)

        if article is None:
            return

        reply = QMessageBox.question(
            self,
            "Brisanje artikla",
            f"Ali res želite izbrisati artikel:\n\n{article[2]}",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            article_repository.delete(article[0])

            self.refresh()
            self.details.clear()

    def current_article(self):

        indexes = self.table.selectionModel().selectedRows()

        if not indexes:
            return None

        row = indexes[0].row()

        article_id = self.model.articles[row][0]

        return article_repository.get_by_id(article_id)

    def clear_search(self):

        self.search.clear()
        self.refresh()

    def _apply_view(self, *_args):
        from app.core.search_engine import invalidate_search_cache

        invalidate_search_cache()
        text = self.search.text().strip()
        articles = self._loader.first()
        unit = self.actions.filter.currentData()
        if unit and unit != "all":
            articles = [row for row in articles if row[3] == unit]
            self.model.refresh(articles)
        else:
            self.model.refresh(articles)
        self._sync_empty_state(text, unit)
        self._update_status()

    def _maybe_more(self, value: int) -> None:
        bar = self.table.verticalScrollBar()
        if self._loader.exhausted or value < bar.maximum() - 12:
            return
        more = self._loader.more()
        unit = self.actions.filter.currentData()
        if unit and unit != "all":
            more = [row for row in more if row[3] == unit]
        self.model.append_rows(more)
        self._update_status()

    def _sync_empty_state(self, text, unit):
        if self.model.rowCount() == 0:
            if text or (unit and unit != "all"):
                self.empty_state.set_message(
                    "Ni zadetkov",
                    "Poskusite z drugim iskanjem ali filtrom enote.",
                )
            else:
                self.empty_state.set_message(
                    "Ni artiklov",
                    "Dodajte prvi artikel v katalog.",
                )
            self.content_stack.setCurrentIndex(0)
        else:
            self.content_stack.setCurrentIndex(1)

    def _update_status(self, *_args):
        self.status.set_count(self.model.rowCount())
        indexes = self.table.selectionModel().selectedRows()
        if not indexes or not self.model.articles:
            self.status.set_selected(None)
            return
        row = indexes[0].row()
        name = self.model.articles[row][2]
        self.status.set_selected(str(name or ""))
