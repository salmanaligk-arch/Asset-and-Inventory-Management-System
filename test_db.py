from db import Database

db = Database()
tables = db.fetch_all("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", [t[0] for t in tables])