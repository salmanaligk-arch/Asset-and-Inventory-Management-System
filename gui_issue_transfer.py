from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QDateEdit, QSpinBox, QDialogButtonBox, QMessageBox, QLabel
from PySide6.QtCore import QDate
from db import Database
from models import AssetTransaction

class IssueTransferDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Issue/Return Assets")
        self.setGeometry(200, 200, 1000, 600)
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.item_combo = QComboBox()
        form_layout.addRow("Item*:", self.item_combo)

        self.year_combo = QComboBox()
        form_layout.addRow("Acquisition Year*:", self.year_combo)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Issue", "Return"])
        form_layout.addRow("Transaction Type*:", self.type_combo)

        self.branch_combo = QComboBox()
        form_layout.addRow("Branch*:", self.branch_combo)

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        form_layout.addRow("Transaction Date:", self.date_edit)

        self.qty_spin = QSpinBox()
        self.qty_spin.setMinimum(1)
        form_layout.addRow("Quantity*:", self.qty_spin)

        self.auth_edit = QLineEdit()
        form_layout.addRow("Authority Ref*:", self.auth_edit)

        self.remarks_edit = QLineEdit()
        form_layout.addRow("Remarks:", self.remarks_edit)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

        # Connect signals after layout
        self.item_combo.currentIndexChanged.connect(self.update_batches)
        self.type_combo.currentIndexChanged.connect(self.update_branch_combo)
        self.branch_combo.currentIndexChanged.connect(self.update_batches)

        # Populate combos
        items = self.db.fetch_all("SELECT item_id, item_name FROM items")
        for it in items:
            self.item_combo.addItem(it[1], it[0])

        self.update_branch_combo()
        self.update_batches()

    def update_batches(self):
        item_id = self.item_combo.currentData()
        self.year_combo.clear()
        if item_id:
            trans_type = self.type_combo.currentText()
            if trans_type == "Issue":
                branch_id = self.db.fetch_one("SELECT branch_id FROM branches WHERE branch_name = 'Store'")[0]
            elif trans_type == "Return":
                branch_id = self.branch_combo.currentData()
            else:
                return
            if branch_id:
                years = self.db.fetch_all("""
                    SELECT ab.acquisition_year, SUM(ab.quantity - COALESCE(it.issued, 0) - COALESCE(ds.disposed, 0)) as total_available
                    FROM asset_batches ab
                    LEFT JOIN (SELECT batch_id, SUM(quantity) as issued FROM asset_transactions WHERE transaction_type IN ('Issue', 'Transfer', 'Return') GROUP BY batch_id) it ON ab.batch_id = it.batch_id
                    LEFT JOIN (SELECT batch_id, SUM(quantity) as disposed FROM asset_disposal GROUP BY batch_id) ds ON ab.batch_id = ds.batch_id
                    WHERE ab.item_id = ? AND ab.branch_id = ? AND (ab.quantity - COALESCE(it.issued, 0) - COALESCE(ds.disposed, 0)) > 0
                    GROUP BY ab.acquisition_year
                """, (item_id, branch_id))
                for yr, total in years:
                    display = f"{yr} ({total})" if yr else f"Unknown ({total})"
                    self.year_combo.addItem(display, yr)

    def update_branch_combo(self):
        trans_type = self.type_combo.currentText()
        self.branch_combo.clear()
        branches = self.db.fetch_all("SELECT branch_id, branch_name FROM branches WHERE branch_name != 'Store'")
        for br in branches:
            self.branch_combo.addItem(br[1], br[0])

    def save(self):
        store_id = self.db.fetch_one("SELECT branch_id FROM branches WHERE branch_name = 'Store'")[0]
        trans_type = self.type_combo.currentText()
        branch_id = self.branch_combo.currentData()
        selected_year = self.year_combo.currentData()
        quantity = self.qty_spin.value()
        if not self.item_combo.currentData() or not trans_type or not branch_id or not selected_year:
            QMessageBox.warning(self, "Warning", "Please fill required fields.")
            return

        # Validate
        if trans_type == "Issue":
            if branch_id == store_id:
                QMessageBox.warning(self, "Warning", "Cannot issue to Store.")
                return
            source_branch_id = store_id
            dest_branch_id = branch_id
        elif trans_type == "Return":
            if branch_id == store_id:
                QMessageBox.warning(self, "Warning", "Cannot return from Store.")
                return
            source_branch_id = branch_id
            dest_branch_id = store_id

        # Get total available for the year
        total_avail = self.db.fetch_one("""
            SELECT SUM(ab.quantity - COALESCE(it.issued, 0) - COALESCE(ds.disposed, 0))
            FROM asset_batches ab
            LEFT JOIN (SELECT batch_id, SUM(quantity) as issued FROM asset_transactions WHERE transaction_type IN ('Issue', 'Transfer', 'Return') GROUP BY batch_id) it ON ab.batch_id = it.batch_id
            LEFT JOIN (SELECT batch_id, SUM(quantity) as disposed FROM asset_disposal GROUP BY batch_id) ds ON ab.batch_id = ds.batch_id
            WHERE ab.item_id = ? AND ab.branch_id = ? AND ab.acquisition_year = ? AND (ab.quantity - COALESCE(it.issued, 0) - COALESCE(ds.disposed, 0)) > 0
        """, (self.item_combo.currentData(), source_branch_id, selected_year))[0] or 0

        if quantity > total_avail:
            QMessageBox.warning(self, "Warning", f"Quantity exceeds available ({total_avail}).")
            return

        # Get batches with the year, ordered by batch_id
        batches = self.db.fetch_all("""
            SELECT ab.batch_id
            FROM asset_batches ab
            LEFT JOIN (SELECT batch_id, SUM(quantity) as issued FROM asset_transactions WHERE transaction_type IN ('Issue', 'Transfer', 'Return') GROUP BY batch_id) it ON ab.batch_id = it.batch_id
            LEFT JOIN (SELECT batch_id, SUM(quantity) as disposed FROM asset_disposal GROUP BY batch_id) ds ON ab.batch_id = ds.batch_id
            WHERE ab.item_id = ? AND ab.branch_id = ? AND ab.acquisition_year = ? AND (ab.quantity - COALESCE(it.issued, 0) - COALESCE(ds.disposed, 0)) > 0
            ORDER BY ab.batch_id
        """, (self.item_combo.currentData(), source_branch_id, selected_year))

        remaining = quantity
        for (batch_id,) in batches:
            if remaining <= 0:
                break
            avail = self.get_available_quantity(batch_id)
            to_trans = min(remaining, avail)
            # Create transaction for this batch
            trans = AssetTransaction(
                batch_id=batch_id,
                transaction_type=trans_type,
                from_branch_id=source_branch_id,
                to_branch_id=dest_branch_id,
                transaction_date=self.date_edit.date().toString("yyyy-MM-dd"),
                quantity=to_trans,
                authority_ref=self.auth_edit.text(),
                remarks=self.remarks_edit.text()
            )
            query = """INSERT INTO asset_transactions (batch_id, transaction_type, from_branch_id, to_branch_id, transaction_date, quantity, authority_ref, remarks)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
            self.db.execute_query(query, (trans.batch_id, trans.transaction_type, trans.from_branch_id, trans.to_branch_id,
                                          trans.transaction_date, trans.quantity, trans.authority_ref, trans.remarks))
            # Create new batch if issue or return
            if trans.transaction_type in ['Issue', 'Return'] and trans.to_branch_id:
                batch_data = self.db.fetch_one("SELECT item_id, cost FROM asset_batches WHERE batch_id = ?", (trans.batch_id,))
                if batch_data:
                    item_id, cost = batch_data
                    to_branch_name = self.db.fetch_one("SELECT branch_name FROM branches WHERE branch_id = ?", (trans.to_branch_id,))[0]
                    if trans.transaction_type == 'Issue':
                        source = f"Issued to {to_branch_name}"
                    elif trans.transaction_type == 'Return':
                        source = f"Returned to {to_branch_name}"
                    new_batch_query = """INSERT INTO asset_batches (item_id, branch_id, acquisition_date, acquisition_method, source, quantity, cost, authority_ref, remarks, acquisition_year)
                                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                    self.db.execute_query(new_batch_query, (item_id, trans.to_branch_id, trans.transaction_date, trans.transaction_type, source, trans.quantity, cost, trans.authority_ref, trans.remarks, selected_year))
            remaining -= to_trans

        QMessageBox.information(self, "Success", "Transaction added successfully.")
        self.accept()

    def get_available_quantity(self, batch_id):
        # Calculate current stock for the batch
        batch_qty = self.db.fetch_one("SELECT quantity FROM asset_batches WHERE batch_id = ?", (batch_id,))[0]
        issued = self.db.fetch_one("SELECT SUM(quantity) FROM asset_transactions WHERE batch_id = ? AND transaction_type IN ('Issue', 'Return')", (batch_id,))[0] or 0
        returned = 0  # Since incoming transactions create new batches
        disposed = self.db.fetch_one("SELECT SUM(quantity) FROM asset_disposal WHERE batch_id = ?", (batch_id,))[0] or 0
        return batch_qty - issued + returned - disposed