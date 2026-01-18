from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLineEdit, QLabel, QMessageBox, QInputDialog, QComboBox, QFormLayout, QDialogButtonBox
from PySide6.QtCore import Qt
from db import Database
from models import SubCategory

class SubCategoriesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Sub-Categories")
        self.setGeometry(200, 200, 400, 300)
        self.db = Database()
        self.init_ui()
        self.load_subcategories()

    def init_ui(self):
        layout = QVBoxLayout()

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("QListWidget { border: 1px solid #ccc; }")
        layout.addWidget(self.list_widget)

        button_layout = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_subcategory)
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_subcategory)
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_subcategory)
        button_layout.addWidget(add_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)

        layout.addLayout(button_layout)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def load_subcategories(self):
        self.list_widget.clear()
        subcats = self.db.fetch_all("""
            SELECT sc.subcategory_id, sc.subcategory_name, c.category_name
            FROM sub_categories sc
            JOIN categories c ON sc.category_id = c.category_id
        """)
        for sub in subcats:
            self.list_widget.addItem(f"{sub[0]}: {sub[1]} ({sub[2]})")

    def get_categories(self):
        return self.db.fetch_all("SELECT category_id, category_name FROM categories")

    def add_subcategory(self):
        dialog = SubCategoryEditDialog(self)
        if dialog.exec() == QDialog.Accepted:
            sub = dialog.get_subcategory()
            query = "INSERT INTO sub_categories (category_id, subcategory_name, remarks) VALUES (?, ?, ?)"
            self.db.execute_query(query, (sub.category_id, sub.subcategory_name, sub.remarks))
            self.load_subcategories()

    def edit_subcategory(self):
        current_item = self.list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a sub-category to edit.")
            return
        sub_id = int(current_item.text().split(":")[0])
        sub_data = self.db.fetch_one("SELECT * FROM sub_categories WHERE subcategory_id = ?", (sub_id,))
        if sub_data:
            dialog = SubCategoryEditDialog(self, sub_data)
            if dialog.exec() == QDialog.Accepted:
                sub = dialog.get_subcategory()
                query = "UPDATE sub_categories SET category_id = ?, subcategory_name = ?, remarks = ? WHERE subcategory_id = ?"
                self.db.execute_query(query, (sub.category_id, sub.subcategory_name, sub.remarks, sub_id))
                self.load_subcategories()

    def delete_subcategory(self):
        current_item = self.list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a sub-category to delete.")
            return
        sub_id = int(current_item.text().split(":")[0])
        reply = QMessageBox.question(self, "Delete", "Are you sure you want to delete this sub-category?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Check if used in items
            count = self.db.fetch_one("SELECT COUNT(*) FROM items WHERE subcategory_id = ?", (sub_id,))[0]
            if count > 0:
                QMessageBox.warning(self, "Warning", "Cannot delete sub-category that has items.")
                return
            self.db.execute_query("DELETE FROM sub_categories WHERE subcategory_id = ?", (sub_id,))
            self.load_subcategories()

class SubCategoryEditDialog(QDialog):
    def __init__(self, parent=None, subcategory_data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Sub-Category" if subcategory_data else "Add Sub-Category")
        self.db = Database()
        self.subcategory_data = subcategory_data
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.cat_combo = QComboBox()
        cats = self.db.fetch_all("SELECT category_id, category_name FROM categories")
        for cat in cats:
            self.cat_combo.addItem(cat[1], cat[0])
        form_layout.addRow("Category*:", self.cat_combo)

        self.name_edit = QLineEdit()
        form_layout.addRow("Sub-Category Name*:", self.name_edit)

        self.remarks_edit = QLineEdit()
        form_layout.addRow("Remarks:", self.remarks_edit)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

        if self.subcategory_data:
            self.load_subcategory()

    def load_subcategory(self):
        self.cat_combo.setCurrentIndex(self.cat_combo.findData(self.subcategory_data[1]))
        self.name_edit.setText(self.subcategory_data[2])
        self.remarks_edit.setText(self.subcategory_data[3] or "")

    def get_subcategory(self):
        return SubCategory(
            category_id=self.cat_combo.currentData(),
            subcategory_name=self.name_edit.text(),
            remarks=self.remarks_edit.text()
        )