# setup_db.py
import sqlite3

# Connect (creates exam.db if it doesn't exist)
conn = sqlite3.connect("exam.db")
cursor = conn.cursor()

# Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    roll_no TEXT PRIMARY KEY,
    name TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY,
    text TEXT NOT NULL,
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    correct_option TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY,
    student_roll TEXT,
    score INTEGER,
    submitted_at TEXT,
    start_time TEXT,
    FOREIGN KEY(student_roll) REFERENCES students(roll_no)
)
""")

conn.commit()
conn.close()

print("Database setup complete!")
