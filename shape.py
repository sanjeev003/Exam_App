import sqlite3

conn = sqlite3.connect("exam.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(results);")
for row in cursor.fetchall():
    print(row)

conn.close()
