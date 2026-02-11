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

#create Notes section
c.execute('''
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    semester INTEGER NOT NULL,
    subject TEXT NOT NULL,
    filename TEXT NOT NULL,
    uploader_email TEXT NOT NULL
)
''')
 # Users table
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0
)
''')

# Subjects table (Admin only)
c.execute('''
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    semester INTEGER NOT NULL
)
''')

# Attendance table
c.execute('''
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    total_classes INTEGER DEFAULT 0,
    attended_classes INTEGER DEFAULT 0,
    FOREIGN KEY(student_id) REFERENCES users(id),
    FOREIGN KEY(subject_id) REFERENCES subjects(id)
)
''')



conn.commit()
conn.close()
print("Tables created successfully.")


