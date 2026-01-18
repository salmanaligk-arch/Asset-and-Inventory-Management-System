from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QDateEdit, QSpinBox, QDialogButtonBox, QMessageBox, QTableWidget, QTableWidgetItem, QHBoxLayout, QPushButton, QHeaderView, QListWidget, QLabel
from PySide6.QtCore import QDate
from db import Database
from models import AssetDisposal

class DisposalDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Asset Disposal")
        self.setGeometry(200, 200, 800, 600)
        self.db = Database()
        self.init_ui()
        self.load_batches()

    def init_ui(self):
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Item", "Acquisition Year", "Available Quantity", "Quantity to Dispose"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        dispose_btn = QPushButton("Dispose Selected")
        dispose_btn.clicked.connect(self.dispose_selected)
        button_layout.addWidget(dispose_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def get_available_quantity(self, batch_id):
        result = self.db.fetch_one("""
            SELECT ab.quantity - COALESCE(issued, 0) + COALESCE(returned, 0) - COALESCE(disposed, 0)
            FROM asset_batches ab
            LEFT JOIN (SELECT batch_id, SUM(quantity) as issued FROM asset_transactions WHERE transaction_type IN ('Issue', 'Transfer') GROUP BY batch_id) it ON ab.batch_id = it.batch_id
            LEFT JOIN (SELECT batch_id, SUM(quantity) as returned FROM asset_transactions WHERE transaction_type = 'Return' GROUP BY batch_id) rt ON ab.batch_id = rt.batch_id
            LEFT JOIN (SELECT batch_id, SUM(quantity) as disposed FROM asset_disposal GROUP BY batch_id) ds ON ab.batch_id = ds.batch_id
            WHERE ab.batch_id = ?
        """, (batch_id,))
        return result[0] if result else 0

    def load_batches(self):
        data = self.db.fetch_all("""
            SELECT i.item_name, ab.acquisition_year, SUM(ab.quantity - COALESCE(issued, 0) + COALESCE(returned, 0) - COALESCE(disposed, 0)) as available
            FROM asset_batches ab
            JOIN items i ON ab.item_id = i.item_id
            JOIN branches b ON ab.branch_id = b.branch_id
            LEFT JOIN (SELECT batch_id, SUM(quantity) as issued FROM asset_transactions WHERE transaction_type IN ('Issue', 'Transfer') GROUP BY batch_id) it ON ab.batch_id = it.batch_id
            LEFT JOIN (SELECT batch_id, SUM(quantity) as returned FROM asset_transactions WHERE transaction_type = 'Return' GROUP BY batch_id) rt ON ab.batch_id = rt.batch_id
            LEFT JOIN (SELECT batch_id, SUM(quantity) as disposed FROM asset_disposal GROUP BY batch_id) ds ON ab.batch_id = ds.batch_id
            WHERE b.branch_name = 'Store' AND (ab.quantity - COALESCE(issued, 0) + COALESCE(returned, 0) - COALESCE(disposed, 0)) > 0
            GROUP BY i.item_id, i.item_name, ab.acquisition_year
            ORDER BY i.item_name, ab.acquisition_year
        """)
        self.table.setRowCount(len(data))
        self.dispose_edits = []
        for row, (item, year, avail) in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(item))
            self.table.setItem(row, 1, QTableWidgetItem(year or ""))
            self.table.setItem(row, 2, QTableWidgetItem(str(avail)))
            edit = QLineEdit()
            edit.setText("0")
            self.table.setCellWidget(row, 3, edit)
            self.dispose_edits.append(edit)

    def dispose_selected(self):
        # Collect items to dispose
        to_dispose = []
        for row in range(self.table.rowCount()):
            qty_text = self.dispose_edits[row].text()
            try:
                qty = int(qty_text)
            except ValueError:
                continue
            if qty > 0:
                item = self.table.item(row, 0).text()
                year = self.table.item(row, 1).text()
                avail = int(self.table.item(row, 2).text())
                if qty > avail:
                    QMessageBox.warning(self, "Warning", f"Quantity to dispose ({qty}) exceeds available ({avail}) for {item} {year}.")
                    return
                to_dispose.append((item, year, qty))

        if not to_dispose:
            QMessageBox.information(self, "Info", "No disposals to perform.")
            return

        # Open confirmation dialog
        dialog = DisposalConfirmDialog(to_dispose, self)
        if dialog.exec() == QDialog.Accepted:
            details = dialog.get_details()
            for item, year, qty in to_dispose:
                # Get item_id
                item_id = self.db.fetch_one("SELECT item_id FROM items WHERE item_name = ?", (item,))[0]
                # Get batches for this item, year, Store
                batches = self.db.fetch_all("""
                    SELECT ab.batch_id
                    FROM asset_batches ab
                    JOIN branches b ON ab.branch_id = b.branch_id
                    LEFT JOIN (SELECT batch_id, SUM(quantity) as issued FROM asset_transactions WHERE transaction_type IN ('Issue', 'Transfer', 'Return') GROUP BY batch_id) it ON ab.batch_id = it.batch_id
                    LEFT JOIN (SELECT batch_id, SUM(quantity) as disposed FROM asset_disposal GROUP BY batch_id) ds ON ab.batch_id = ds.batch_id
                    WHERE ab.item_id = ? AND (ab.acquisition_year = ? OR ab.acquisition_year IS NULL) AND b.branch_name = 'Store' AND (ab.quantity - COALESCE(it.issued, 0) - COALESCE(ds.disposed, 0)) > 0
                    ORDER BY ab.batch_id
                """, (item_id, year))
                remaining = qty
                for (batch_id,) in batches:
                    if remaining <= 0:
                        break
                    avail = self.get_available_quantity(batch_id)
                    to_disp = min(remaining, avail)
                    disp = AssetDisposal(
                        batch_id=batch_id,
                        disposal_date=details['date'],
                        quantity=to_disp,
                        disposal_method=details['method'],
                        authority_ref=details['authority'],
                        remarks=details['remarks']
                    )
                    query = """INSERT INTO asset_disposal (batch_id, disposal_date, quantity, disposal_method, authority_ref, remarks)
                               VALUES (?, ?, ?, ?, ?, ?)"""
                    self.db.execute_query(query, (disp.batch_id, disp.disposal_date, disp.quantity, disp.disposal_method,
                                                  disp.authority_ref, disp.remarks))
                    remaining -= to_disp
            QMessageBox.information(self, "Success", "Disposals completed.")
            self.load_batches()

class DisposalConfirmDialog(QDialog):
    def __init__(self, to_dispose, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Disposal")
        self.to_dispose = to_dispose
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Show list of items to dispose
        label = QLabel("Items to Dispose:")
        layout.addWidget(label)
        list_widget = QListWidget()
        for item, year, qty in self.to_dispose:
            list_widget.addItem(f"{year}: {item} - Qty {qty}")
        layout.addWidget(list_widget)

        form_layout = QFormLayout()

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        form_layout.addRow("Disposal Date*:", self.date_edit)

        self.method_edit = QLineEdit()
        self.method_edit.setText("Condemnation")
        form_layout.addRow("Disposal Method*:", self.method_edit)

        self.auth_edit = QLineEdit()
        form_layout.addRow("Authority Ref*:", self.auth_edit)

        self.remarks_edit = QLineEdit()
        form_layout.addRow("Remarks:", self.remarks_edit)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_details(self):
        return {
            'date': self.date_edit.date().toString("yyyy-MM-dd"),
            'method': self.method_edit.text(),
            'authority': self.auth_edit.text(),
            'remarks': self.remarks_edit.text()
        }