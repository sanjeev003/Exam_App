import sqlite3
conn = sqlite3.connect("exam.db")
cur = conn.cursor()
cur.execute("SELECT id, correct_option FROM questions")
print(cur.fetchall())
conn.close()
