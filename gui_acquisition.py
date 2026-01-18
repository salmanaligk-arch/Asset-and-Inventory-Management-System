from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QDialogButtonBox, QMessageBox
from PySide6.QtCore import QDate
from db import Database
from models import AssetBatch

class AcquisitionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Asset Acquisition")
        self.setGeometry(200, 200, 400, 300)
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.item_combo = QComboBox()
        items = self.db.fetch_all("SELECT item_id, item_name FROM items")
        for it in items:
            self.item_combo.addItem(it[1], it[0])
        form_layout.addRow("Item*:", self.item_combo)

        self.branch_combo = QComboBox()
        branches = self.db.fetch_all("SELECT branch_id, branch_name FROM branches WHERE branch_name = 'Store'")
        for br in branches:
            self.branch_combo.addItem(br[1], br[0])
        self.branch_combo.setEnabled(False)  # Disable selection, force Store
        form_layout.addRow("Branch*:", self.branch_combo)

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        form_layout.addRow("Acquisition Date:", self.date_edit)

        self.method_edit = QLineEdit()
        form_layout.addRow("Acquisition Method*:", self.method_edit)

        self.source_edit = QLineEdit()
        form_layout.addRow("Source:", self.source_edit)

        self.qty_spin = QSpinBox()
        self.qty_spin.setMinimum(1)
        form_layout.addRow("Quantity*:", self.qty_spin)

        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setMinimum(0.0)
        form_layout.addRow("Cost:", self.cost_spin)

        self.auth_edit = QLineEdit()
        form_layout.addRow("Authority Ref:", self.auth_edit)

        self.requisition_year_edit = QLineEdit()
        form_layout.addRow("Acquisition Year*:", self.requisition_year_edit)

        self.remarks_edit = QLineEdit()
        form_layout.addRow("Remarks:", self.remarks_edit)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def save(self):
        batch = AssetBatch(
            item_id=self.item_combo.currentData(),
            branch_id=self.branch_combo.currentData(),
            acquisition_date=self.date_edit.date().toString("yyyy-MM-dd"),
            acquisition_method=self.method_edit.text(),
            source=self.source_edit.text(),
            quantity=self.qty_spin.value(),
            cost=self.cost_spin.value(),
            authority_ref=self.auth_edit.text(),
            remarks=self.remarks_edit.text(),
            acquisition_year=self.requisition_year_edit.text()
        )
        if not batch.item_id or not batch.branch_id or not batch.acquisition_method or not batch.acquisition_year:
            QMessageBox.warning(self, "Warning", "Please fill required fields.")
            return
        query = """INSERT INTO asset_batches (item_id, branch_id, acquisition_date, acquisition_method, source, quantity, cost, authority_ref, remarks, acquisition_year)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        self.db.execute_query(query, (batch.item_id, batch.branch_id, batch.acquisition_date, batch.acquisition_method,
                                      batch.source, batch.quantity, batch.cost, batch.authority_ref, batch.remarks, batch.acquisition_year))
        QMessageBox.information(self, "Success", "Asset batch added successfully.")
        self.accept()