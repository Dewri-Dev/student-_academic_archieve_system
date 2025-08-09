import sqlite3

# Connect to the database
conn = sqlite3.connect("database.db")
c = conn.cursor()

# Fetch all uploaded materials
c.execute("SELECT * FROM materials")
rows = c.fetchall()

# Display each row
for row in rows:
    print(row)

conn.close()
