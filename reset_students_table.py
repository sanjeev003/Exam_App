import sqlite3

conn = sqlite3.connect("exam.db")
cursor = conn.cursor()

# Drop the old table completely
cursor.execute("DROP TABLE IF EXISTS students")

# Create the correct table
cursor.execute("""
CREATE TABLE students (
    roll_no TEXT PRIMARY KEY,
    name TEXT NOT NULL
)
""")

conn.commit()
conn.close()

print("Students table recreated successfully!")
