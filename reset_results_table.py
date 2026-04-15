# import sqlite3

# conn = sqlite3.connect("exam.db")
# cursor = conn.cursor()

# # Drop the old results table
# cursor.execute("DROP TABLE IF EXISTS results")

# # Create the correct results table with local time
# cursor.execute("""
# CREATE TABLE results (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     student_roll TEXT,
#     score INTEGER,
#     submitted_at TIMESTAMP DEFAULT (datetime('now','localtime')),
#     FOREIGN KEY(student_roll) REFERENCES students(roll_no)
# )
# """)

# conn.commit()
# conn.close()

# print("Results table recreated successfully with local time!")


import sqlite3

conn = sqlite3.connect("exam.db")
cursor = conn.cursor()

# Drop the old results table
cursor.execute("DROP TABLE IF EXISTS results")

# Create the results table with question tracking
cursor.execute("""
CREATE TABLE results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_roll TEXT,
    score INTEGER,
    submitted_at TEXT,
    start_time TEXT,
    question_ids TEXT,   -- store the 30 question IDs assigned
    FOREIGN KEY(student_roll) REFERENCES students(roll_no)
)
""")

conn.commit()
conn.close()

print("Results table recreated successfully with question tracking!")
