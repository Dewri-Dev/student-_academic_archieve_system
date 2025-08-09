import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

# Optional: create table if missing
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password TEXT,
    is_admin INTEGER
)
''')

# Insert admin if not already exists
c.execute("INSERT OR IGNORE INTO users (email, password, is_admin) VALUES (?, ?, ?)",
          ("nayan@astu.ac.in", "nayan2004", 1))

conn.commit()
conn.close()

print("Admin user created (or already exists).")


