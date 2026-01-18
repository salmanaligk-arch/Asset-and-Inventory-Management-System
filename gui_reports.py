from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QMessageBox
from db import Database

class StockRegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stock Register")
        self.setGeometry(200, 200, 800, 600)
        self.db = Database()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setStyleSheet("QTableWidget { border: 1px solid #ccc; gridline-color: #ddd; } QHeaderView::section { background-color: #f0f0f0; border: 1px solid #ccc; }")
        layout.addWidget(self.table)
        button_layout = QHBoxLayout()
        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self.export_csv)
        button_layout.addWidget(export_btn)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def load_data(self):
        # Simple stock register: item, total acquired (original), disposed, remaining
        data = self.db.fetch_all("""
            SELECT i.item_name, SUM(ab.quantity) as acquired, SUM(COALESCE(ds.disposed, 0)) as disposed
            FROM asset_batches ab
            JOIN items i ON ab.item_id = i.item_id
            LEFT JOIN (SELECT batch_id, SUM(quantity) as disposed FROM asset_disposal GROUP BY batch_id) ds ON ab.batch_id = ds.batch_id
            WHERE ab.acquisition_method NOT IN ('Issue', 'Return')
            GROUP BY i.item_id, i.item_name
        """)
        self.table.setRowCount(0)  # Start with 0 rows
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Item", "Acquired", "Disposed", "Remaining"])
        row = 0
        for name, acq, disp in data:
            acq = acq or 0
            disp = disp or 0
            rem = acq - disp
            if rem > 0:
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(name))
                self.table.setItem(row, 1, QTableWidgetItem(str(acq)))
                self.table.setItem(row, 2, QTableWidgetItem(str(disp)))
                self.table.setItem(row, 3, QTableWidgetItem(str(rem)))
                row += 1

    def export_csv(self):
        import csv
        from PySide6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if filename:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                headers = ["Item", "Acquired", "Disposed", "Remaining"]
                writer.writerow(headers)
                for row in range(self.table.rowCount()):
                    row_data = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "Export", "Data exported to CSV successfully.")

class BranchBalanceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Branch-wise Balance")
        self.setGeometry(200, 200, 800, 600)
        self.db = Database()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setStyleSheet("QTableWidget { border: 1px solid #ccc; gridline-color: #ddd; } QHeaderView::section { background-color: #f0f0f0; border: 1px solid #ccc; }")
        layout.addWidget(self.table)
        button_layout = QHBoxLayout()
        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self.export_csv)
        button_layout.addWidget(export_btn)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def load_data(self):
        # Branch, item, balance
        data = self.db.fetch_all("""
            SELECT b.branch_name, i.item_name,
                   SUM(ab.quantity) - 
                   (SELECT COALESCE(SUM(at.quantity), 0) FROM asset_transactions at WHERE at.batch_id = ab.batch_id AND at.transaction_type IN ('Issue', 'Transfer')) -
                   (SELECT COALESCE(SUM(at.quantity), 0) FROM asset_transactions at WHERE at.batch_id = ab.batch_id AND at.transaction_type = 'Return') -
                   (SELECT COALESCE(SUM(ad.quantity), 0) FROM asset_disposal ad WHERE ad.batch_id = ab.batch_id) as balance
            FROM asset_batches ab
            JOIN branches b ON ab.branch_id = b.branch_id
            JOIN items i ON ab.item_id = i.item_id
            GROUP BY b.branch_id, b.branch_name, i.item_id, i.item_name
            HAVING balance > 0
        """)
        self.table.setRowCount(len(data))
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Branch", "Item", "Balance"])
        for row, (br, it, bal) in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(br))
            self.table.setItem(row, 1, QTableWidgetItem(it))
            self.table.setItem(row, 2, QTableWidgetItem(str(bal)))

    def export_csv(self):
        import csv
        from PySide6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if filename:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                headers = ["Branch", "Item", "Balance"]
                writer.writerow(headers)
                for row in range(self.table.rowCount()):
                    row_data = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "Export", "Data exported to CSV successfully.")

class DisposalReportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Disposal Report")
        self.setGeometry(200, 200, 800, 600)
        self.db = Database()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setStyleSheet("QTableWidget { border: 1px solid #ccc; gridline-color: #ddd; } QHeaderView::section { background-color: #f0f0f0; border: 1px solid #ccc; }")
        layout.addWidget(self.table)
        button_layout = QHBoxLayout()
        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self.export_csv)
        button_layout.addWidget(export_btn)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def load_data(self):
        data = self.db.fetch_all("""
            SELECT i.item_name, ad.disposal_date, ad.quantity, ad.disposal_method, ad.authority_ref
            FROM asset_disposal ad
            JOIN asset_batches ab ON ad.batch_id = ab.batch_id
            JOIN items i ON ab.item_id = i.item_id
            ORDER BY ad.disposal_date DESC
        """)
        self.table.setRowCount(len(data))
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Item", "Date", "Quantity", "Method", "Authority"])
        for row, (it, dt, qty, meth, auth) in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(it))
            self.table.setItem(row, 1, QTableWidgetItem(dt))
            self.table.setItem(row, 2, QTableWidgetItem(str(qty)))
            self.table.setItem(row, 3, QTableWidgetItem(meth))
            self.table.setItem(row, 4, QTableWidgetItem(auth or ""))

    def export_csv(self):
        import csv
        from PySide6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if filename:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                headers = ["Item", "Date", "Quantity", "Method", "Authority"]
                writer.writerow(headers)
                for row in range(self.table.rowCount()):
                    row_data = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "Export", "Data exported to CSV successfully.")

class AcquisitionHistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Acquisition History")
        self.setGeometry(200, 200, 800, 600)
        self.db = Database()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setStyleSheet("QTableWidget { border: 1px solid #ccc; gridline-color: #ddd; } QHeaderView::section { background-color: #f0f0f0; border: 1px solid #ccc; }")
        layout.addWidget(self.table)
        button_layout = QHBoxLayout()
        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self.export_csv)
        button_layout.addWidget(export_btn)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def load_data(self):
        data = self.db.fetch_all("""
            SELECT i.item_name, b.branch_name, ab.acquisition_date, ab.acquisition_year, ab.quantity, ab.acquisition_method, ab.source
            FROM asset_batches ab
            JOIN items i ON ab.item_id = i.item_id
            JOIN branches b ON ab.branch_id = b.branch_id
            WHERE ab.acquisition_method NOT IN ('Issue', 'Return')
            ORDER BY ab.acquisition_date DESC
        """)
        self.table.setRowCount(len(data))
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Item", "Branch", "Date", "Acquisition Year", "Quantity", "Method", "Source"])
        for row, (it, br, dt, ay, qty, meth, src) in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(it))
            self.table.setItem(row, 1, QTableWidgetItem(br))
            self.table.setItem(row, 2, QTableWidgetItem(dt))
            self.table.setItem(row, 3, QTableWidgetItem(ay or ""))
            self.table.setItem(row, 4, QTableWidgetItem(str(qty)))
            self.table.setItem(row, 5, QTableWidgetItem(meth))
            self.table.setItem(row, 6, QTableWidgetItem(src or ""))

    def export_csv(self):
        import csv
        from PySide6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if filename:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                headers = ["Item", "Branch", "Date", "Acquisition Year", "Quantity", "Method", "Source"]
                writer.writerow(headers)
                for row in range(self.table.rowCount()):
                    row_data = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "Export", "Data exported to CSV successfully.")

class TransactionHistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Transaction History")
        self.setGeometry(200, 200, 1000, 600)
        self.db = Database()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setStyleSheet("QTableWidget { border: 1px solid #ccc; gridline-color: #ddd; } QHeaderView::section { background-color: #f0f0f0; border: 1px solid #ccc; }")
        layout.addWidget(self.table)
        button_layout = QHBoxLayout()
        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self.export_csv)
        button_layout.addWidget(export_btn)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def load_data(self):
        data = self.db.fetch_all("""
            SELECT at.transaction_date, at.transaction_type, fb.branch_name as from_branch, tb.branch_name as to_branch,
                   i.item_name, at.quantity, at.authority_ref, at.remarks
            FROM asset_transactions at
            LEFT JOIN branches fb ON at.from_branch_id = fb.branch_id
            LEFT JOIN branches tb ON at.to_branch_id = tb.branch_id
            JOIN asset_batches ab ON at.batch_id = ab.batch_id
            JOIN items i ON ab.item_id = i.item_id
            ORDER BY at.transaction_date DESC
        """)
        self.table.setRowCount(len(data))
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["Date", "Type", "From Branch", "To Branch", "Item", "Quantity", "Authority", "Remarks"])
        for row, (dt, typ, fb, tb, it, qty, auth, rem) in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(dt))
            self.table.setItem(row, 1, QTableWidgetItem(typ))
            self.table.setItem(row, 2, QTableWidgetItem(fb or ""))
            self.table.setItem(row, 3, QTableWidgetItem(tb or ""))
            self.table.setItem(row, 4, QTableWidgetItem(it))
            self.table.setItem(row, 5, QTableWidgetItem(str(qty)))
            self.table.setItem(row, 6, QTableWidgetItem(auth or ""))
            self.table.setItem(row, 7, QTableWidgetItem(rem or ""))

    def export_csv(self):
        import csv
        from PySide6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if filename:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                headers = ["Date", "Type", "From Branch", "To Branch", "Item", "Quantity", "Authority", "Remarks"]
                writer.writerow(headers)
                for row in range(self.table.rowCount()):
                    row_data = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "Export", "Data exported to CSV successfully.")