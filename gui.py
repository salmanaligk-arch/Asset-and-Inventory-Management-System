import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStatusBar, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt
from db import Database

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Assets and Inventory Management System (AIMS)")
        self.setGeometry(100, 100, 800, 500)

        self.db = Database()
        self.ensure_store_branch()
        self.create_menu()
        self.create_status_bar()
        self.set_central_widget()

    def create_menu(self):
        menubar = self.menuBar()

        # Master Data Menu
        master_menu = menubar.addMenu("Master Data")
        master_menu.addAction("Categories", self.open_categories)
        master_menu.addAction("Sub-Categories", self.open_subcategories)
        master_menu.addAction("Branches", self.open_branches)
        master_menu.addAction("Items", self.open_items)

        # Transactions Menu
        trans_menu = menubar.addMenu("Transactions")
        trans_menu.addAction("Acquisition", self.open_acquisition)
        trans_menu.addAction("Issue/Return", self.open_issue_transfer)
        trans_menu.addAction("Disposal", self.open_disposal)

        # Reports Menu
        reports_menu = menubar.addMenu("Reports")
        reports_menu.addAction("Summary", self.open_stock_register)
        reports_menu.addAction("Branch-wise Balance", self.open_branch_balance)
        reports_menu.addAction("Disposal Report", self.open_disposal_report)
        reports_menu.addAction("Acquisition History", self.open_acquisition_history)
        reports_menu.addAction("Transaction History", self.open_transaction_history)

        # Help Menu
        help_menu = menubar.addMenu("Help")
        help_menu.addAction("About", self.show_about)

    def create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def ensure_store_branch(self):
        store = self.db.fetch_one("SELECT branch_id FROM branches WHERE branch_name = 'Store'")
        if not store:
            self.db.execute_query("INSERT INTO branches (branch_name, address, remarks) VALUES ('Store', 'Central Store', 'Default central branch for acquisitions and disposals')")

    def load_stock_register(self):
        db = Database()
        data = db.fetch_all("""
            SELECT c.category_name, sc.subcategory_name, i.item_name, b.branch_name, batch_bal.acquisition_year, SUM(batch_bal.balance) as total_balance
            FROM (
                SELECT ab.batch_id, ab.item_id, ab.branch_id, ab.acquisition_year,
                       ab.quantity - COALESCE(issued, 0) - COALESCE(disposed, 0) as balance
                FROM asset_batches ab
                LEFT JOIN (SELECT batch_id, SUM(quantity) as issued FROM asset_transactions WHERE transaction_type IN ('Issue', 'Transfer', 'Return') GROUP BY batch_id) it ON ab.batch_id = it.batch_id
                LEFT JOIN (SELECT batch_id, SUM(quantity) as disposed FROM asset_disposal GROUP BY batch_id) ds ON ab.batch_id = ds.batch_id
            ) batch_bal
            JOIN items i ON batch_bal.item_id = i.item_id
            JOIN categories c ON i.category_id = c.category_id
            JOIN sub_categories sc ON i.subcategory_id = sc.subcategory_id
            JOIN branches b ON batch_bal.branch_id = b.branch_id
            GROUP BY c.category_name, sc.subcategory_name, i.item_name, b.branch_name, batch_bal.acquisition_year
            HAVING total_balance > 0
            ORDER BY c.category_name, sc.subcategory_name, i.item_name, b.branch_name, batch_bal.acquisition_year
        """)
        self.stock_table.setRowCount(len(data))
        self.stock_table.setColumnCount(6)
        self.stock_table.setHorizontalHeaderLabels(["Category", "Sub-Category", "Item", "Branch", "Acquisition Year", "Balance"])
        for row, (cat, sub, it, br, ay, bal) in enumerate(data):
            self.stock_table.setItem(row, 0, QTableWidgetItem(cat))
            self.stock_table.setItem(row, 1, QTableWidgetItem(sub))
            self.stock_table.setItem(row, 2, QTableWidgetItem(it))
            self.stock_table.setItem(row, 3, QTableWidgetItem(br))
            self.stock_table.setItem(row, 4, QTableWidgetItem(ay or ""))
            self.stock_table.setItem(row, 5, QTableWidgetItem(str(bal)))

    def export_stock_csv(self):
        import csv
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        filename, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if filename:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                headers = ["Category", "Sub-Category", "Item", "Branch", "Acquisition Year", "Balance"]
                writer.writerow(headers)
                for row in range(self.stock_table.rowCount()):
                    row_data = []
                    for col in range(self.stock_table.columnCount()):
                        item = self.stock_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "Export", "Stock data exported to CSV successfully.")

    def set_central_widget(self):
        central_widget = QWidget()
        layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        label = QLabel("Stock Register")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(label)

        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self.export_stock_csv)
        header_layout.addWidget(export_btn)

        layout.addLayout(header_layout)

        self.stock_table = QTableWidget()
        self.stock_table.setStyleSheet("QTableWidget { border: 1px solid #ccc; gridline-color: #ddd; } QHeaderView::section { background-color: #f0f0f0; border: 1px solid #ccc; }")
        layout.addWidget(self.stock_table)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        self.load_stock_register()

    def open_categories(self):
        from gui_categories import CategoriesDialog
        dialog = CategoriesDialog(self)
        dialog.exec()

    def open_subcategories(self):
        from gui_subcategories import SubCategoriesDialog
        dialog = SubCategoriesDialog(self)
        dialog.exec()

    def open_branches(self):
        from gui_branches import BranchesDialog
        dialog = BranchesDialog(self)
        dialog.exec()

    def open_items(self):
        from gui_items import ItemsDialog
        dialog = ItemsDialog(self)
        dialog.exec()

    def open_acquisition(self):
        from gui_acquisition import AcquisitionDialog
        dialog = AcquisitionDialog(self)
        dialog.exec()
        self.load_stock_register()

    def open_issue_transfer(self):
        from gui_issue_transfer import IssueTransferDialog
        dialog = IssueTransferDialog(self)
        dialog.exec()
        self.load_stock_register()

    def open_disposal(self):
        from gui_disposal import DisposalDialog
        dialog = DisposalDialog(self)
        dialog.exec()
        self.load_stock_register()

    def open_stock_register(self):
        from gui_reports import StockRegisterDialog
        dialog = StockRegisterDialog(self)
        dialog.exec()

    def open_branch_balance(self):
        from gui_reports import BranchBalanceDialog
        dialog = BranchBalanceDialog(self)
        dialog.exec()

    def open_disposal_report(self):
        from gui_reports import DisposalReportDialog
        dialog = DisposalReportDialog(self)
        dialog.exec()

    def open_acquisition_history(self):
        from gui_reports import AcquisitionHistoryDialog
        dialog = AcquisitionHistoryDialog(self)
        dialog.exec()

    def open_transaction_history(self):
        from gui_reports import TransactionHistoryDialog
        dialog = TransactionHistoryDialog(self)
        dialog.exec()

    def show_about(self):
        from PySide6.QtWidgets import QMessageBox
        about_text = """
        Assets and Inventory Management System
        Version 1.0

        Instructions:

        - The Store is the main branch where all acquisitions and disposals occur.
        - Acquisitions: Add new assets to the Store by selecting items, quantities, and acquisition details.
        - Disposals: Remove assets from the Store by selecting items and quantities to dispose, providing disposal details.
        - Issue/Return: Transfer assets from the Store to branches (Issue) or return them back to the Store from branches (Return).
          - Issue: Select a branch and item/year to issue quantities to that branch.
          - Return: Select a branch and item/year to return quantities back to the Store.

        Reports provide summaries of stock, branch balances, and transaction histories.
        """
        QMessageBox.about(self, "Help", about_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())