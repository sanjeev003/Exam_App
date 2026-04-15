import sqlite3

conn = sqlite3.connect("exam.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE results ADD COLUMN start_time TEXT;")
    print("Column 'start_time' added successfully.")
except sqlite3.OperationalError as e:
    print("Error:", e)

conn.commit()
conn.close()
