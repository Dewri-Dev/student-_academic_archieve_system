import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

# Create users table (if not already there)
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    password TEXT,
    is_admin INTEGER
)
""")

# Create papers table
c.execute("""
CREATE TABLE IF NOT EXISTS papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    semester TEXT,
    year INTEGER,
    subject TEXT,
    drive_link TEXT
)
""")
#create user activity log
c.execute('''
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT,
    action TEXT,
    timestamp TEXT
)
''')

conn.commit()
conn.close()
print("Tables created successfully.")


