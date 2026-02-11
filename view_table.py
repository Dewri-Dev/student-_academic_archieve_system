import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

# Show all tables
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", c.fetchall())

# Example: Show all users
c.execute("SELECT * FROM users;")
print("Users:", c.fetchall())

conn.close()