from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLineEdit, QLabel, QMessageBox, QInputDialog, QComboBox, QFormLayout, QDialogButtonBox
from PySide6.QtCore import Qt
from db import Database
from models import Item

class ItemsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Items")
        self.setGeometry(200, 200, 1000, 600)
        self.db = Database()
        self.init_ui()
        self.load_items()

    def init_ui(self):
        layout = QVBoxLayout()

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("QListWidget { border: 1px solid #ccc; }")
        layout.addWidget(self.list_widget)

        button_layout = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_item)
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_item)
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_item)
        button_layout.addWidget(add_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)

        layout.addLayout(button_layout)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def load_items(self):
        self.list_widget.clear()
        items = self.db.fetch_all("""
            SELECT i.item_id, i.item_name, c.category_name, sc.subcategory_name
            FROM items i
            JOIN categories c ON i.category_id = c.category_id
            JOIN sub_categories sc ON i.subcategory_id = sc.subcategory_id
        """)
        for it in items:
            self.list_widget.addItem(f"{it[0]}: {it[1]} ({it[2]} - {it[3]})")

    def get_categories(self):
        return self.db.fetch_all("SELECT category_id, category_name FROM categories")

    def get_subcategories(self, cat_id):
        return self.db.fetch_all("SELECT subcategory_id, subcategory_name FROM sub_categories WHERE category_id = ?", (cat_id,))

    def add_item(self):
        dialog = ItemEditDialog(self)
        if dialog.exec() == QDialog.Accepted:
            item = dialog.get_item()
            if not item.category_id or not item.subcategory_id:
                QMessageBox.warning(self, "Warning", "Please select a category and subcategory.")
                return
            # Check if govt_property_code is required
            item_count = self.db.fetch_one("SELECT COUNT(*) FROM items")[0]
            if item_count > 0 and not item.govt_property_code:
                QMessageBox.warning(self, "Warning", "Govt Property Code is required for additional items.")
                return
            query = """INSERT INTO items (item_name, category_id, subcategory_id, specification, govt_property_code, remarks)
                       VALUES (?, ?, ?, ?, ?, ?)"""
            self.db.execute_query(query, (item.item_name, item.category_id, item.subcategory_id, item.specification,
                                          item.govt_property_code, item.remarks))
            self.load_items()

    def edit_item(self):
        current_item = self.list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select an item to edit.")
            return
        item_id = int(current_item.text().split(":")[0])
        item_data = self.db.fetch_one("SELECT * FROM items WHERE item_id = ?", (item_id,))
        if item_data:
            dialog = ItemEditDialog(self, item_data)
            if dialog.exec() == QDialog.Accepted:
                item = dialog.get_item()
                if not item.category_id or not item.subcategory_id:
                    QMessageBox.warning(self, "Warning", "Please select a category and subcategory.")
                    return
                query = """UPDATE items SET item_name = ?, category_id = ?, subcategory_id = ?, specification = ?,
                          govt_property_code = ?, remarks = ? WHERE item_id = ?"""
                self.db.execute_query(query, (item.item_name, item.category_id, item.subcategory_id, item.specification,
                                              item.govt_property_code, item.remarks, item_id))
                self.load_items()

    def delete_item(self):
        current_item = self.list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select an item to delete.")
            return
        item_id = int(current_item.text().split(":")[0])
        reply = QMessageBox.question(self, "Delete", "Are you sure you want to delete this item?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Check if used in batches
            count = self.db.fetch_one("SELECT COUNT(*) FROM asset_batches WHERE item_id = ?", (item_id,))[0]
            if count > 0:
                QMessageBox.warning(self, "Warning", "Cannot delete item that has asset batches.")
                return
            self.db.execute_query("DELETE FROM items WHERE item_id = ?", (item_id,))
            self.load_items()

class ItemEditDialog(QDialog):
    def __init__(self, parent=None, item_data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Item" if item_data else "Add Item")
        self.db = Database()
        self.item_data = item_data
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        form_layout.addRow("Item Name*:", self.name_edit)

        self.cat_combo = QComboBox()
        cats = self.db.fetch_all("SELECT category_id, category_name FROM categories")
        for cat in cats:
            self.cat_combo.addItem(cat[1], cat[0])
        self.cat_combo.currentIndexChanged.connect(self.update_subcats)
        form_layout.addRow("Category*:", self.cat_combo)

        self.subcat_combo = QComboBox()
        form_layout.addRow("Sub-Category*:", self.subcat_combo)

        self.spec_edit = QLineEdit()
        form_layout.addRow("Specification:", self.spec_edit)

        self.code_edit = QLineEdit()
        form_layout.addRow("Govt Property Code*:", self.code_edit)

        self.remarks_edit = QLineEdit()
        form_layout.addRow("Remarks:", self.remarks_edit)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

        if self.item_data:
            self.load_item()

        self.update_subcats()

    def update_subcats(self):
        cat_id = self.cat_combo.currentData()
        self.subcat_combo.clear()
        subcats = self.db.fetch_all("SELECT subcategory_id, subcategory_name FROM sub_categories WHERE category_id = ?", (cat_id,))
        for sub in subcats:
            self.subcat_combo.addItem(sub[1], sub[0])

    def load_item(self):
        self.name_edit.setText(self.item_data[1])
        self.cat_combo.setCurrentIndex(self.cat_combo.findData(self.item_data[2]))
        self.update_subcats()
        self.subcat_combo.setCurrentIndex(self.subcat_combo.findData(self.item_data[3]))
        self.spec_edit.setText(self.item_data[4] or "")
        self.code_edit.setText(self.item_data[5] or "")
        self.remarks_edit.setText(self.item_data[6] or "")

    def get_item(self):
        return Item(
            item_name=self.name_edit.text(),
            category_id=self.cat_combo.currentData(),
            subcategory_id=self.subcat_combo.currentData(),
            specification=self.spec_edit.text(),
            govt_property_code=self.code_edit.text(),
            remarks=self.remarks_edit.text()
        )