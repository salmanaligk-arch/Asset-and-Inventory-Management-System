from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLineEdit, QLabel, QMessageBox, QInputDialog, QFormLayout, QDialogButtonBox
from PySide6.QtCore import Qt
from db import Database
from models import Category

class CategoriesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Categories")
        self.setGeometry(200, 200, 400, 300)
        self.db = Database()
        self.init_ui()
        self.load_categories()

    def init_ui(self):
        layout = QVBoxLayout()

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("QListWidget { border: 1px solid #ccc; }")
        layout.addWidget(self.list_widget)

        button_layout = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_category)
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_category)
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_category)
        button_layout.addWidget(add_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)

        layout.addLayout(button_layout)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def load_categories(self):
        self.list_widget.clear()
        categories = self.db.fetch_all("SELECT category_id, category_name FROM categories")
        for cat in categories:
            self.list_widget.addItem(f"{cat[0]}: {cat[1]}")

    def add_category(self):
        dialog = CategoryEditDialog(self)
        if dialog.exec() == QDialog.Accepted:
            cat = dialog.get_category()
            query = "INSERT INTO categories (category_name, remarks) VALUES (?, ?)"
            self.db.execute_query(query, (cat.category_name, cat.remarks))
            self.load_categories()

    def edit_category(self):
        current_item = self.list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a category to edit.")
            return
        cat_id = int(current_item.text().split(":")[0])
        cat_data = self.db.fetch_one("SELECT * FROM categories WHERE category_id = ?", (cat_id,))
        if cat_data:
            dialog = CategoryEditDialog(self, cat_data)
            if dialog.exec() == QDialog.Accepted:
                cat = dialog.get_category()
                query = "UPDATE categories SET category_name = ?, remarks = ? WHERE category_id = ?"
                self.db.execute_query(query, (cat.category_name, cat.remarks, cat_id))
                self.load_categories()

    def delete_category(self):
        current_item = self.list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a category to delete.")
            return
        cat_id = int(current_item.text().split(":")[0])
        reply = QMessageBox.question(self, "Delete", "Are you sure you want to delete this category?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Check if used in subcategories
            count = self.db.fetch_one("SELECT COUNT(*) FROM sub_categories WHERE category_id = ?", (cat_id,))[0]
            if count > 0:
                QMessageBox.warning(self, "Warning", "Cannot delete category that has subcategories.")
                return
            self.db.execute_query("DELETE FROM categories WHERE category_id = ?", (cat_id,))
            self.load_categories()

class CategoryEditDialog(QDialog):
    def __init__(self, parent=None, category_data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Category" if category_data else "Add Category")
        self.category_data = category_data
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        form_layout.addRow("Category Name*:", self.name_edit)

        self.remarks_edit = QLineEdit()
        form_layout.addRow("Remarks:", self.remarks_edit)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

        if self.category_data:
            self.load_category()

    def load_category(self):
        self.name_edit.setText(self.category_data[1])
        self.remarks_edit.setText(self.category_data[2] or "")

    def get_category(self):
        return Category(
            category_name=self.name_edit.text(),
            remarks=self.remarks_edit.text()
        )