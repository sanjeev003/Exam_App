# init_db.py
import psycopg2
import psycopg2.extras
import os

def create_tables():
    conn = psycopg2.connect(
        os.environ["DATABASE_URL"],
        cursor_factory=psycopg2.extras.DictCursor
    )
    cur = conn.cursor()

    # Create tables if they don't exist
    cur.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id SERIAL PRIMARY KEY,
        text TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL,
        option_d TEXT NOT NULL,
        correct_option TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS results (
        id SERIAL PRIMARY KEY,
        roll_no TEXT NOT NULL,
        name TEXT,
        score INTEGER,
        submitted_at TIMESTAMP,
        responses JSON
    );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("Tables created successfully!")

if __name__ == "__main__":
    create_tables()
