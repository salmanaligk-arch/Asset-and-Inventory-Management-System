import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name='assets_inventory.db'):
        self.db_name = db_name
        self.connection = None
        self.cursor = None
        self.create_tables()

    def connect(self):
        self.connection = sqlite3.connect(self.db_name)
        self.cursor = self.connection.cursor()

    def disconnect(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def create_tables(self):
        self.connect()
        try:
            # Categories table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_name TEXT NOT NULL UNIQUE,
                    remarks TEXT
                )
            ''')

            # Sub-Categories table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS sub_categories (
                    subcategory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER NOT NULL,
                    subcategory_name TEXT NOT NULL,
                    remarks TEXT,
                    FOREIGN KEY (category_id) REFERENCES categories (category_id)
                )
            ''')

            # Branches table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS branches (
                    branch_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    branch_name TEXT NOT NULL UNIQUE,
                    address TEXT,
                    remarks TEXT
                )
            ''')

            # Items table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS items (
                    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_name TEXT NOT NULL,
                    category_id INTEGER NOT NULL,
                    subcategory_id INTEGER NOT NULL,
                    specification TEXT,
                    govt_property_code TEXT UNIQUE,
                    remarks TEXT,
                    FOREIGN KEY (category_id) REFERENCES categories (category_id),
                    FOREIGN KEY (subcategory_id) REFERENCES sub_categories (subcategory_id)
                )
            ''')

            # Asset Batches table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS asset_batches (
                    batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER NOT NULL,
                    branch_id INTEGER NOT NULL,
                    acquisition_date DATE NOT NULL,
                    acquisition_method TEXT NOT NULL,
                    source TEXT,
                    quantity INTEGER NOT NULL,
                    cost REAL,
                    authority_ref TEXT,
                    remarks TEXT,
                    acquisition_year TEXT,
                    FOREIGN KEY (item_id) REFERENCES items (item_id),
                    FOREIGN KEY (branch_id) REFERENCES branches (branch_id)
                )
            ''')

            # Asset Transactions table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS asset_transactions (
                    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id INTEGER NOT NULL,
                    transaction_type TEXT NOT NULL,
                    from_branch_id INTEGER,
                    to_branch_id INTEGER,
                    transaction_date DATE NOT NULL,
                    quantity INTEGER NOT NULL,
                    authority_ref TEXT,
                    remarks TEXT,
                    FOREIGN KEY (batch_id) REFERENCES asset_batches (batch_id),
                    FOREIGN KEY (from_branch_id) REFERENCES branches (branch_id),
                    FOREIGN KEY (to_branch_id) REFERENCES branches (branch_id)
                )
            ''')

            # Disposal table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS asset_disposal (
                    disposal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id INTEGER NOT NULL,
                    disposal_date DATE NOT NULL,
                    quantity INTEGER NOT NULL,
                    disposal_method TEXT NOT NULL,
                    authority_ref TEXT,
                    remarks TEXT,
                    FOREIGN KEY (batch_id) REFERENCES asset_batches (batch_id)
                )
            ''')

            # Users table (optional)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL
                )
            ''')

            self.connection.commit()
            # Migration: drop unit column if exists
            try:
                self.cursor.execute("ALTER TABLE items DROP COLUMN unit")
                self.connection.commit()
            except sqlite3.OperationalError:
                pass  # column already dropped or not supported
        except Exception as e:
            print(f"Error creating tables: {e}")
        finally:
            self.disconnect()

    def execute_query(self, query, params=()):
        self.connect()
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"Error executing query: {e}")
            return None
        finally:
            self.disconnect()

    def fetch_all(self, query, params=()):
        self.connect()
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error fetching data: {e}")
            return []
        finally:
            self.disconnect()

    def fetch_one(self, query, params=()):
        self.connect()
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchone()
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None
        finally:
            self.disconnect()