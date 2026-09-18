from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QTableView,
    QHeaderView,
    QSplitter,
    QMessageBox,
)

from app.modules.articles.models.article_table_model import ArticleTableModel
from app.modules.articles.article_dialog import ArticleDialog
from app.modules.articles.article_details import ArticleDetails
from app.database.article_repository import article_repository
from app.widgets.messages import ui_error_boundary


class ArticlePage(QWidget):

    def __init__(self):
        super().__init__()

        self.setObjectName("ArticlePage")

        layout = QVBoxLayout(self)

        title = QLabel("Artikli")
        title.setStyleSheet("""
            font-size:24px;
            font-weight:bold;
            padding:8px;
        """)
        layout.addWidget(title)

        top_layout = QHBoxLayout()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Išči artikel...")

        self.btn_new = QPushButton("+ Nov artikel")
        self.btn_edit = QPushButton("✏️ Uredi")
        self.btn_delete = QPushButton("🗑 Izbriši")
        self.btn_refresh = QPushButton("🔄 Osveži")

        top_layout.addWidget(self.search)
        top_layout.addWidget(self.btn_new)
        top_layout.addWidget(self.btn_edit)
        top_layout.addWidget(self.btn_delete)
        top_layout.addWidget(self.btn_refresh)

        layout.addLayout(top_layout)

        self.table = QTableView()

        self.model = ArticleTableModel([])
        self.table.setModel(self.model)

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setAlternatingRowColors(True)

        self.details = ArticleDetails()

        splitter = QSplitter()
        splitter.addWidget(self.table)
        splitter.addWidget(self.details)
        splitter.setSizes([700, 350])

        layout.addWidget(splitter)

        self.search.textChanged.connect(self.search_article)
        self.btn_new.clicked.connect(self.new_article)
        self.btn_edit.clicked.connect(self.edit_selected_article)
        self.btn_delete.clicked.connect(self.delete_article)
        self.btn_refresh.clicked.connect(self.refresh)

        self.table.clicked.connect(self.show_details)
        self.table.doubleClicked.connect(self.edit_article)

        self.details.editButton.clicked.connect(
            self.edit_selected_article
        )

        self.refresh()

    @ui_error_boundary("Artiklov ni mogoče naložiti")
    def refresh(self):
        articles = article_repository.get_all()
        self.model.refresh(articles)

    @ui_error_boundary("Iskanja ni mogoče izvesti")
    def search_article(self, text):
        text = text.strip()

        if text:
            articles = article_repository.search(text)
        else:
            articles = article_repository.get_all()

        self.model.refresh(articles)

    @ui_error_boundary("Artikla ni mogoče shraniti")
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

    @ui_error_boundary("Podrobnosti ni mogoče prikazati")
    def show_details(self, index):
        row = index.row()

        article_id = self.model.articles[row][0]

        article = article_repository.get_by_id(article_id)

        if article:
            self.details.load_article(article)

    def edit_selected_article(self):

        if self.details.article_id is None:
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

    @ui_error_boundary("Artikla ni mogoče posodobiti")
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

    @ui_error_boundary("Artikla ni mogoče izbrisati")
    def delete_article(self):
        if self.details.article_id is None:
            return

        article = article_repository.get_by_id(
            self.details.article_id
        )

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

            self.details.article_id = None
            self.details.code.setText("-")
            self.details.name.setText("-")
            self.details.description.setText("-")
            self.details.unit.setText("-")
            self.details.price.setText("-")
            self.details.vat.setText("-")

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
