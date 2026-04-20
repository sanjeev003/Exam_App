from flask import Flask, render_template, request, redirect, url_for, session, Response
import sqlite3
import csv
from datetime import datetime
import pytz
import os
import psycopg2
import psycopg2.extras


app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Needed for sessions

def get_db_connection():
    conn = psycopg2.connect(
        os.environ["DATABASE_URL"],   # Render sets this automatically
        cursor_factory=psycopg2.extras.DictCursor
    )
    return conn


# ---------------- STUDENT ROUTES ----------------

# Root URL → redirect to login
@app.route('/')
def index():
    return redirect(url_for('login_page'))


# Show login page
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

# Handle login form submission
@app.route('/login', methods=['POST'])
def login_submit():
    roll_no = request.form['roll_no']

    conn = psycopg2.connect(
        os.environ["DATABASE_URL"],
        cursor_factory=psycopg2.extras.DictCursor
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM students WHERE roll_no=%s", (roll_no,))
    student = cur.fetchone()
    cur.close()
    conn.close()

    if student is None:
        return "Invalid Roll No. Please contact admin."

    # ✅ set roll_no in session
    session['student_logged_in'] = True
    session['roll_no'] = student['roll_no']
    session['student_name'] = student['name']

    return redirect(url_for('exam'))



@app.route('/logout')
def logout():
    # Clear the session so the admin is logged out
    session.clear()
    # Redirect back to the admin login page
    return redirect(url_for('admin_login'))

# Exam page (GET + POST)
@app.route('/exam', methods=['GET', 'POST'])
def exam():
    if request.method == 'POST':
        roll_no = request.form['roll_no']
        session['roll_no'] = roll_no   # ✅ use consistent session key
    else:
        roll_no = session.get('roll_no')

    if not roll_no:
        return redirect(url_for('login_page'))  # ✅ fixed endpoint name

    conn = psycopg2.connect(
        os.environ["DATABASE_URL"],
        cursor_factory=psycopg2.extras.DictCursor
    )
    cur = conn.cursor()

    # Get student record
    cur.execute("SELECT * FROM students WHERE roll_no = %s", (roll_no,))
    student = cur.fetchone()

    if not student:
        cur.close()
        conn.close()
        return render_template("invalid_roll.html")

    # Check if already submitted
    cur.execute("SELECT * FROM results WHERE roll_no = %s AND score IS NOT NULL", (roll_no,))
    existing = cur.fetchone()
    if existing:
        cur.close()
        conn.close()
        return render_template("already_submitted.html")

    ist = pytz.timezone('Asia/Kolkata')
    cur.execute("SELECT start_time, question_ids FROM results WHERE roll_no = %s", (roll_no,))
    existing_result = cur.fetchone()

    if not existing_result or existing_result['start_time'] is None:
        # ✅ store as datetime object, not string
        start_time = datetime.now(ist)

        # Pick 30 random questions
        cur.execute("SELECT id FROM questions ORDER BY RANDOM() LIMIT 30")
        questions = cur.fetchall()
        question_ids = ",".join(str(q['id']) for q in questions)

        cur.execute(
            "INSERT INTO results (roll_no, start_time, question_ids) VALUES (%s, %s, %s) "
            "ON CONFLICT (roll_no) DO UPDATE SET start_time = EXCLUDED.start_time, question_ids = EXCLUDED.question_ids",
            (roll_no, start_time, question_ids)
        )
        conn.commit()

        # Reload full question data
        cur.execute(f"SELECT * FROM questions WHERE id IN ({question_ids})")
        questions = cur.fetchall()
    else:
        start_time = existing_result['start_time']
        question_ids = existing_result['question_ids']
        cur.execute(f"SELECT * FROM questions WHERE id IN ({question_ids})")
        questions = cur.fetchall()

    cur.close()
    conn.close()

    # ✅ pass ISO string to template for JS timer
    return render_template(
        'exam.html',
        student=student,
        questions=questions,
        start_time=start_time.isoformat()
    )


# @app.route("/initdb")
# def initdb():
#     from init_db import create_tables
#     create_tables()
#     return "Tables created successfully!"


# # Submission route with time enforcement
# @app.route('/submit', methods=['POST'])
# def submit():
#     roll_no = session.get('student_roll')
#     if not roll_no:
#         return "Session expired or invalid access."

#     conn = get_db_connection()
#     session_data = conn.execute("SELECT start_time, question_ids FROM results WHERE student_roll=?", (roll_no,)).fetchone()

#     if not session_data or not session_data['start_time']:
#         conn.close()
#         return "Exam session invalid."

#     ist = pytz.timezone('Asia/Kolkata')
#     start_time = ist.localize(datetime.strptime(session_data['start_time'], "%Y-%m-%d %H:%M:%S"))
#     now = datetime.now(ist)
#     elapsed_minutes = (now - start_time).total_seconds() / 60

#     if elapsed_minutes > 30:
#         conn.close()
#         session.pop('student_roll', None)
#         return "Time is up! Your exam session expired."

#     # Grade only the assigned questions
#     question_ids = session_data['question_ids']
#     questions = conn.execute(f"SELECT * FROM questions WHERE id IN ({question_ids})").fetchall()
#     score = 0
#     for q in questions:
#         user_answer = request.form.get(str(q['id']))
#         print(f"Question ID: {q['id']}, User answer: {user_answer}, Correct answer: {q['correct_option']}")
#         if user_answer == q['correct_option']:
#             score += 1

#     conn.execute("UPDATE results SET score=?, submitted_at=? WHERE student_roll=?",
#                  (score, now.strftime("%Y-%m-%d %H:%M:%S"), roll_no))
#     conn.commit()
#     conn.close()

#     session.pop('student_roll', None)
#     return render_template('result.html', score=score)

# Submission route with time enforcement (Postgres version)
@app.route('/submit', methods=['POST'])
def submit():
    roll_no = session.get('roll_no')   # ✅ use roll_no consistently
    if not roll_no:
        return "Session expired or invalid access."

    conn = psycopg2.connect(
        os.environ["DATABASE_URL"],
        cursor_factory=psycopg2.extras.DictCursor
    )
    cur = conn.cursor()

    # Fetch exam session data
    cur.execute(
        "SELECT start_time, question_ids FROM results WHERE roll_no=%s",
        (roll_no,)
    )
    session_data = cur.fetchone()

    if not session_data or not session_data['start_time']:
        cur.close()
        conn.close()
        return "Exam session invalid."

    ist = pytz.timezone('Asia/Kolkata')
    start_time_value = session_data['start_time']

    # ✅ Handle both datetime and string cases safely
    if isinstance(start_time_value, datetime):
        # If Postgres already returns datetime, just convert timezone
        start_time = start_time_value.astimezone(ist)
    else:
        # If stored as string, parse it
        start_time = ist.localize(datetime.strptime(start_time_value, "%Y-%m-%d %H:%M:%S"))

    now = datetime.now(ist)
    elapsed_minutes = (now - start_time).total_seconds() / 60

    # ✅ Optional: add 1-minute grace period
    if elapsed_minutes > 31:
        cur.close()
        conn.close()
        session.pop('roll_no', None)
        return "Time is up! Your exam session expired."

    # Grade only the assigned questions
    question_ids = session_data['question_ids']
    cur.execute(f"SELECT * FROM questions WHERE id IN ({question_ids})")
    questions = cur.fetchall()

    score = 0
    feedback = []

    for q in questions:
        user_answer = request.form.get(str(q['id']))
        print(f"Question ID: {q['id']}, User answer: {user_answer}, Correct answer key: {q['correct_option']}")

        options_map = {
            "option_a": q["option_a"],
            "option_b": q["option_b"],
            "option_c": q["option_c"],
            "option_d": q["option_d"],
        }

        correct_key = q['correct_option']
        correct_text = options_map.get(correct_key, "⚠ Invalid DB value")
        chosen_text = options_map.get(user_answer, "Not answered")

        feedback.append({
            "text": q['text'],
            "chosen": chosen_text,
            "correct": correct_text,
            "is_correct": (user_answer == correct_key)
        })

        if user_answer == correct_key:
            score += 1

    # Save responses JSON into results table
    cur.execute(
        "UPDATE results SET score=%s, submitted_at=%s, responses=%s WHERE roll_no=%s",
        (score, now.strftime("%Y-%m-%d %H:%M:%S"), json.dumps(feedback), roll_no)
    )

    conn.commit()
    cur.close()
    conn.close()

    session.pop('roll_no', None)
    return render_template('result.html', score=score, feedback=feedback)


# ---------------- ADMIN ROUTES ----------------

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return "Invalid credentials!"
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')

import json

@app.route('/admin/results')
def view_results():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = psycopg2.connect(
        os.environ["DATABASE_URL"],
        cursor_factory=psycopg2.extras.DictCursor
    )
    cur = conn.cursor()

    cur.execute("""
        SELECT s.roll_no, s.name,
               COALESCE(r.score::text, '-') AS score,
               COALESCE(r.submitted_at::text, '-') AS submitted_at,
               COALESCE(r.start_time::text, '-') AS start_time,
               r.responses,
               r.question_ids
        FROM students s
        LEFT JOIN (
            SELECT DISTINCT ON (roll_no) roll_no, score, submitted_at, start_time, responses, question_ids
            FROM results
            ORDER BY roll_no, submitted_at DESC
        ) r ON s.roll_no = r.roll_no
        ORDER BY s.roll_no
    """)
    results = cur.fetchall()

    cur.close()
    conn.close()

    processed_results = []

    for r in results:
        responses = []

        if r['responses']:
            if isinstance(r['responses'], str):
                try:
                    responses = json.loads(r['responses'])
                except Exception:
                    responses = []
            elif isinstance(r['responses'], list):
                responses = r['responses']

        processed_results.append({
            **r,
            "responses_parsed": responses
        })

    return render_template('all_results.html', results=processed_results)


@app.route('/admin/export')
def export_results():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = psycopg2.connect(
        os.environ["DATABASE_URL"],
        cursor_factory=psycopg2.extras.DictCursor
    )
    cur = conn.cursor()

    # ✅ Use DISTINCT ON to get latest result per student
    cur.execute("""
        SELECT s.roll_no, s.name,
               COALESCE(r.score::text, '-') AS score,
               COALESCE(r.submitted_at::text, '-') AS submitted_at,
               COALESCE(r.start_time::text, '-') AS start_time
        FROM students s
        LEFT JOIN (
            SELECT DISTINCT ON (roll_no) roll_no, score, submitted_at, start_time
            FROM results
            ORDER BY roll_no, submitted_at DESC
        ) r ON s.roll_no = r.roll_no
        ORDER BY s.roll_no
    """)
    results = cur.fetchall()

    cur.close()
    conn.close()

    output = Response(content_type="text/csv")
    writer = csv.writer(output.stream)
    writer.writerow(["Roll No", "Name", "Score", "Submitted At", "Start Time"])
    for r in results:
        writer.writerow([r['roll_no'], r['name'], r['score'], r['submitted_at'], r['start_time']])
    output.headers["Content-Disposition"] = "attachment; filename=results.csv"
    return output


@app.route('/admin/clear_scores')
def clear_scores():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute("UPDATE results SET score = NULL, submitted_at = NULL, start_time = NULL")
    conn.commit()
    cur.close()
    conn.close()

    return "All scores and submission times cleared successfully!"


@app.route('/admin/remove_result/<roll_no>', methods=['POST'])
def remove_result(roll_no):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute("DELETE FROM results WHERE roll_no=%s", (roll_no,))
    conn.commit()
    cur.close()
    conn.close()

    return f"Result for Roll No {roll_no} removed. Student can re‑attempt exam."

from io import StringIO
@app.route('/admin/export_with_responses')
def export_with_responses():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = psycopg2.connect(
        os.environ["DATABASE_URL"],
        cursor_factory=psycopg2.extras.DictCursor
    )
    cur = conn.cursor()

    cur.execute("""
        SELECT s.roll_no, s.name,
               COALESCE(r.score::text, '-') AS score,
               COALESCE(r.submitted_at::text, '-') AS submitted_at,
               COALESCE(r.start_time::text, '-') AS start_time,
               r.responses
        FROM students s
        LEFT JOIN (
            SELECT DISTINCT ON (roll_no) roll_no, score, submitted_at, start_time, responses
            FROM results
            ORDER BY roll_no, submitted_at DESC
        ) r ON s.roll_no = r.roll_no
        ORDER BY s.roll_no
    """)
    results = cur.fetchall()

    cur.close()
    conn.close()

    # ✅ FIX: Use StringIO instead of Response.stream
    si = StringIO()
    writer = csv.writer(si)

    writer.writerow([
        "Roll No", "Name", "Score", "Submitted At",
        "Start Time", "Question", "Chosen", "Correct", "Is Correct"
    ])

    for r in results:
        responses = []

        if r['responses']:
            if isinstance(r['responses'], str):
                try:
                    responses = json.loads(r['responses'])
                except Exception:
                    responses = []
            elif isinstance(r['responses'], list):
                responses = r['responses']

        # ✅ If no responses, still write basic row (optional)
        if not responses:
            writer.writerow([
                r['roll_no'],
                r['name'],
                r['score'],
                r['submitted_at'],
                r['start_time'],
                "", "", "", ""
            ])

        for ans in responses:
            writer.writerow([
                r['roll_no'],
                r['name'],
                r['score'],
                r['submitted_at'],
                r['start_time'],
                ans.get('text', ''),
                ans.get('chosen', ''),
                ans.get('correct', ''),
                "Correct" if ans.get('is_correct') else "Wrong"
            ])

    # ✅ Return CSV properly
    output = Response(si.getvalue(), mimetype="text/csv")
    output.headers["Content-Disposition"] = "attachment; filename=results_with_responses.csv"

    return output


@app.route('/admin/export_student/<roll_no>')
def export_student(roll_no):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = psycopg2.connect(
        os.environ["DATABASE_URL"],
        cursor_factory=psycopg2.extras.DictCursor
    )
    cur = conn.cursor()

    # ✅ Use DISTINCT ON to get the latest result for this student
    cur.execute("""
        SELECT s.roll_no, s.name,
               COALESCE(r.score::text, '-') AS score,
               COALESCE(r.submitted_at::text, '-') AS submitted_at,
               COALESCE(r.start_time::text, '-') AS start_time,
               r.responses
        FROM students s
        LEFT JOIN (
            SELECT DISTINCT ON (roll_no) roll_no, score, submitted_at, start_time, responses
            FROM results
            WHERE roll_no = %s
            ORDER BY roll_no, submitted_at DESC
        ) r ON s.roll_no = r.roll_no
        WHERE s.roll_no = %s
    """, (roll_no, roll_no))
    r = cur.fetchone()

    cur.close()
    conn.close()

    output = Response(content_type="text/csv")
    writer = csv.writer(output.stream)
    writer.writerow(["Roll No", "Name", "Score", "Submitted At", "Start Time", "Question", "Chosen", "Correct", "Is Correct"])

    responses = []
    if r and r['responses']:
        try:
            responses = json.loads(r['responses'])
        except Exception:
            responses = []

    for ans in responses:
        writer.writerow([
            r['roll_no'],
            r['name'],
            r['score'],
            r['submitted_at'],
            r['start_time'],
            ans.get('text', ''),
            ans.get('chosen', ''),
            ans.get('correct', ''),
            "Correct" if ans.get('is_correct') else "Wrong"
        ])

    output.headers["Content-Disposition"] = f"attachment; filename={roll_no}_responses.csv"
    return output



@app.route('/admin/students')
def manage_students():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = psycopg2.connect(
        os.environ["DATABASE_URL"],
        cursor_factory=psycopg2.extras.DictCursor
    )
    cur = conn.cursor()

    cur.execute("SELECT * FROM students ORDER BY roll_no")
    students = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('students.html', students=students)


@app.route('/admin/add_student', methods=['POST'])
def add_student():
    roll_no = request.form['roll_no']
    name = request.form['name']

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute("INSERT INTO students (roll_no, name) VALUES (%s, %s)", (roll_no, name))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('manage_students'))


@app.route('/admin/update_student/<roll_no>', methods=['POST'])
def update_student(roll_no):
    new_name = request.form['new_name']

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute("UPDATE students SET name=%s WHERE roll_no=%s", (new_name, roll_no))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('manage_students'))


@app.route('/admin/remove_student/<roll_no>', methods=['POST'])
def remove_student(roll_no):
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute("DELETE FROM students WHERE roll_no=%s", (roll_no,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('manage_students'))


@app.route('/admin/questions')
def manage_questions():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = psycopg2.connect(
        os.environ["DATABASE_URL"],
        cursor_factory=psycopg2.extras.DictCursor
    )
    cur = conn.cursor()

    cur.execute("SELECT * FROM questions ORDER BY id")
    questions = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('questions.html', questions=questions)


@app.route('/admin/add_question', methods=['POST'])
def add_question():
    text = request.form['text']
    option_a = request.form['option_a']
    option_b = request.form['option_b']
    option_c = request.form['option_c']
    option_d = request.form['option_d']
    correct_option = request.form['correct_option'].strip()

    # 🔹 Normalize input: handle both lowercase and uppercase
    mapping = {
        "a": "option_a", "A": "option_a",
        "b": "option_b", "B": "option_b",
        "c": "option_c", "C": "option_c",
        "d": "option_d", "D": "option_d"
    }
    correct_option = mapping.get(correct_option, correct_option)

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO questions (text, option_a, option_b, option_c, option_d, correct_option) VALUES (%s, %s, %s, %s, %s, %s)",
        (text, option_a, option_b, option_c, option_d, correct_option)
    )
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('manage_questions'))


@app.route('/admin/update_question/<int:id>', methods=['POST'])
def update_question(id):
    new_text = request.form['new_text']

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute("UPDATE questions SET text=%s WHERE id=%s", (new_text, id))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('manage_questions'))


@app.route('/admin/remove_question/<int:id>', methods=['POST'])
def remove_question(id):
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute("DELETE FROM questions WHERE id=%s", (id,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('manage_questions'))



# ---------------- MAIN ----------------    

if __name__ == '__main__':
    app.run(debug=True)
