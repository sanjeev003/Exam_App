import sqlite3

# Replace with your actual database file name
conn = sqlite3.connect("setup_db.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT id, text, option_a, option_b, option_c, option_d, correct_option FROM questions LIMIT 5")
rows = cur.fetchall()

for row in rows:
    print(dict(row))
