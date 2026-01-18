from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLineEdit, QLabel, QMessageBox, QInputDialog, QComboBox, QFormLayout, QDialogButtonBox
from PySide6.QtCore import Qt
from db import Database
from models import Branch

class BranchesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Branches")
        self.setGeometry(200, 200, 400, 300)
        self.db = Database()
        self.init_ui()
        self.load_branches()

    def init_ui(self):
        layout = QVBoxLayout()

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("QListWidget { border: 1px solid #ccc; }")
        layout.addWidget(self.list_widget)

        button_layout = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_branch)
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_branch)
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_branch)
        button_layout.addWidget(add_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)

        layout.addLayout(button_layout)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def load_branches(self):
        self.list_widget.clear()
        branches = self.db.fetch_all("SELECT branch_id, branch_name FROM branches")
        for br in branches:
            self.list_widget.addItem(f"{br[0]}: {br[1]}")

    def add_branch(self):
        dialog = BranchEditDialog(self)
        if dialog.exec() == QDialog.Accepted:
            br = dialog.get_branch()
            query = "INSERT INTO branches (branch_name, address, remarks) VALUES (?, ?, ?)"
            self.db.execute_query(query, (br.branch_name, br.address, br.remarks))
            self.load_branches()

    def edit_branch(self):
        current_item = self.list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a branch to edit.")
            return
        br_id = int(current_item.text().split(":")[0])
        br_data = self.db.fetch_one("SELECT * FROM branches WHERE branch_id = ?", (br_id,))
        if br_data:
            dialog = BranchEditDialog(self, br_data)
            if dialog.exec() == QDialog.Accepted:
                br = dialog.get_branch()
                query = "UPDATE branches SET branch_name = ?, address = ?, remarks = ? WHERE branch_id = ?"
                self.db.execute_query(query, (br.branch_name, br.address, br.remarks, br_id))
                self.load_branches()

    def delete_branch(self):
        current_item = self.list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a branch to delete.")
            return
        br_id = int(current_item.text().split(":")[0])
        br_name = self.db.fetch_one("SELECT branch_name FROM branches WHERE branch_id = ?", (br_id,))[0]
        if br_name == "Store":
            QMessageBox.warning(self, "Warning", "Cannot delete the Store branch.")
            return
        reply = QMessageBox.question(self, "Delete", "Are you sure you want to delete this branch?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Check if used
            count_batches = self.db.fetch_one("SELECT COUNT(*) FROM asset_batches WHERE branch_id = ?", (br_id,))[0]
            count_trans = self.db.fetch_one("SELECT COUNT(*) FROM asset_transactions WHERE from_branch_id = ? OR to_branch_id = ?", (br_id, br_id))[0]
            if count_batches > 0 or count_trans > 0:
                QMessageBox.warning(self, "Warning", "Cannot delete branch that has associated assets or transactions.")
                return
            self.db.execute_query("DELETE FROM branches WHERE branch_id = ?", (br_id,))
            self.load_branches()

class BranchEditDialog(QDialog):
    def __init__(self, parent=None, branch_data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Branch" if branch_data else "Add Branch")
        self.branch_data = branch_data
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        form_layout.addRow("Branch Name*:", self.name_edit)

        self.address_edit = QLineEdit()
        form_layout.addRow("Address:", self.address_edit)

        self.remarks_edit = QLineEdit()
        form_layout.addRow("Remarks:", self.remarks_edit)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

        if self.branch_data:
            self.load_branch()

    def load_branch(self):
        self.name_edit.setText(self.branch_data[1])
        self.address_edit.setText(self.branch_data[2] or "")
        self.remarks_edit.setText(self.branch_data[3] or "")

    def get_branch(self):
        return Branch(
            branch_name=self.name_edit.text(),
            address=self.address_edit.text(),
            remarks=self.remarks_edit.text()
        )