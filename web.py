
from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
import os

app = Flask(__name__)

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "students.db")


# DATABASE CONNECTION
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


# CREATE DATABASE TABLES
def create_table():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            course TEXT,
            contact TEXT,
            email TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            obtained REAL NOT NULL,
            maximum REAL NOT NULL,
            UNIQUE(student_id, subject),
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)

    conn.commit()
    conn.close()


# CALCULATE RESULT
def calculate_result(student_id):
    conn = get_db()

    records = conn.execute(
        "SELECT * FROM marks WHERE student_id=?",
        (student_id,)
    ).fetchall()

    conn.close()

    total = sum(m["obtained"] for m in records)
    maximum = sum(m["maximum"] for m in records)

    percentage = (total / maximum * 100) if maximum else 0

    if not records:
        grade = "Not Available"
        result = "No Marks"
    elif any(m["obtained"] < 0.4 * m["maximum"] for m in records):
        grade = "F"
        result = "Fail"
    else:
        result = "Pass"
        if percentage >= 90:
            grade = "A+"
        elif percentage >= 80:
            grade = "A"
        elif percentage >= 70:
            grade = "B"
        elif percentage >= 60:
            grade = "C"
        elif percentage >= 50:
            grade = "D"
        elif percentage >= 40:
            grade = "E"
        else:
            grade = "F"

    return records, total, maximum, percentage, grade, result


# COMMON WEBSITE DESIGN
PAGE = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Student Management System</title>

<style>
* {box-sizing:border-box}

body {
    margin:0;
    font-family:Arial,sans-serif;
    background:#f1f5fb;
    color:#24334b;
}

header {
    background:#173b70;
    color:white;
    padding:22px 15px;
    text-align:center;
}

header h2 {margin:0 0 8px}

nav {
    background:#24518c;
    padding:13px;
    display:flex;
    flex-wrap:wrap;
    justify-content:center;
    gap:10px;
}

nav a {
    color:white;
    text-decoration:none;
    padding:9px 12px;
    border-radius:6px;
    font-size:14px;
}

nav a:hover {background:#102f5d}

.container {
    width:94%;
    max-width:1050px;
    margin:25px auto;
}

.card {
    background:white;
    padding:20px;
    margin-bottom:20px;
    border-radius:12px;
    box-shadow:0 3px 12px #00000012;
}

.cards {
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
    gap:15px;
}

.stat {
    background:#e5efff;
    padding:20px;
    text-align:center;
    border-radius:10px;
}

.stat h2 {color:#173b70}

input,select {
    width:100%;
    padding:12px;
    margin:7px 0 15px;
    border:1px solid #ccd5e2;
    border-radius:7px;
    font-size:15px;
}

button,.btn {
    background:#20539a;
    color:white;
    padding:11px 16px;
    border:0;
    border-radius:7px;
    text-decoration:none;
    cursor:pointer;
    display:inline-block;
    font-size:14px;
}

.danger {background:#c0392b}
.green {background:#218754}
.grey {background:#65758b}

table {
    width:100%;
    border-collapse:collapse;
    min-width:550px;
}

th,td {
    padding:12px;
    border-bottom:1px solid #ddd;
    text-align:left;
}

th {background:#e6effc}

.tablebox {overflow-x:auto}

.notice {
    background:#e4f6e9;
    color:#176b37;
    padding:12px;
    border-radius:7px;
    margin-bottom:15px;
}

.error {
    background:#ffe6e6;
    color:#a00000;
    padding:12px;
    border-radius:7px;
}

h3 {color:#173b70}

footer {
    text-align:center;
    padding:20px;
    color:#64748b;
}
</style>
</head>

<body>

<header>
<h2>Student Management System</h2>
<p>Student Records | Subject Marks | Result Management</p>
</header>

<nav>
<a href="/">Dashboard</a>
<a href="/add">Add Student</a>
<a href="/students">All Students</a>
</nav>

<div class="container">
{{ content|safe }}
</div>

<footer>
Student Management System | Developed by Anshu Kumari and Group member Trishna Sharma using Python & Flask
</footer>

</body>
</html>
"""


def show(content, **data):
    return render_template_string(PAGE, content=render_template_string(content, **data))


# DASHBOARD
@app.route("/")
def home():
    conn = get_db()

    total = conn.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    subjects = conn.execute(
        "SELECT COUNT(DISTINCT subject) FROM marks"
    ).fetchone()[0]

    marked = conn.execute(
        "SELECT COUNT(DISTINCT student_id) FROM marks"
    ).fetchone()[0]

    conn.close()

    content = """
    <h2>Welcome to Student Management System</h2>

    <div class="cards">
        <div class="stat">
            <h2>{{total}}</h2>
            <p>Total Students</p>
        </div>

        <div class="stat">
            <h2>{{subjects}}</h2>
            <p>Total Subjects</p>
        </div>

        <div class="stat">
            <h2>{{marked}}</h2>
            <p>Students with Marks</p>
        </div>
    </div>

    <div class="card">
        <h3>Project Features</h3>
        <p>✔ Add and manage student records</p>
        <p>✔ Search student details</p>
        <p>✔ Add different subject marks</p>
        <p>✔ Automatically calculate percentage</p>
        <p>✔ Generate student result and grade</p>
        <a class="btn" href="/add">Add New Student</a>
    </div>
    """

    return show(content, total=total, subjects=subjects, marked=marked)


# ADD STUDENT
@app.route("/add", methods=["GET", "POST"])
def add_student():

    message = ""

    if request.method == "POST":
        roll = request.form.get("roll", "").strip()
        name = request.form.get("name", "").strip()
        course = request.form.get("course", "").strip()
        contact = request.form.get("contact", "").strip()
        email = request.form.get("email", "").strip()

        if not roll or not name:
            message = "Roll Number and Name are required."
        else:
            conn = get_db()

            try:
                conn.execute("""
                    INSERT INTO students
                    (roll,name,course,contact,email)
                    VALUES(?,?,?,?,?)
                """, (roll,name,course,contact,email))

                conn.commit()
                conn.close()

                return redirect(url_for("students"))

            except sqlite3.IntegrityError:
                message = "This Roll Number already exists."
                conn.close()

    content = """
    <div class="card">
    <h2>Add New Student</h2>

    {% if message %}
    <div class="error">{{message}}</div>
    {% endif %}

    <form method="POST">
        <label>Roll Number *</label>
        <input name="roll" required>

        <label>Student Name *</label>
        <input name="name" required>

        <label>Course</label>
        <select name="course">
            <option>BCA</option>
            <option>BBA</option>
            <option>MCA</option>
            <option>MBA</option>
            <option>Other</option>
        </select>

        <label>Contact Number</label>
        <input name="contact">

        <label>Email</label>
        <input name="email" type="email">

        <button type="submit">Save Student</button>
    </form>
    </div>
    """

    return show(content, message=message)


# VIEW STUDENTS AND SEARCH
@app.route("/students")
def students():

    search = request.args.get("search", "")

    conn = get_db()

    records = conn.execute("""
        SELECT * FROM students
        WHERE name LIKE ? OR roll LIKE ?
        ORDER BY id DESC
    """, ("%" + search + "%", "%" + search + "%")).fetchall()

    conn.close()

    content = """
    <div class="card">
    <h2>All Students</h2>

    <form method="GET">
        <input name="search" value="{{search}}"
        placeholder="Search by Name or Roll Number">
        <button>Search</button>
        <a href="/students" class="btn grey">Reset</a>
    </form>

    <div class="tablebox">
    <table>
    <tr>
        <th>Roll</th>
        <th>Name</th>
        <th>Course</th>
        <th>Actions</th>
    </tr>

    {% for s in records %}
    <tr>
        <td>{{s.roll}}</td>
        <td>{{s.name}}</td>
        <td>{{s.course}}</td>
        <td>
            <a class="btn" href="/marks/{{s.id}}">Marks</a>
            <a class="btn green" href="/result/{{s.id}}">Result</a>
            <a class="btn grey" href="/edit/{{s.id}}">Edit</a>
            <a class="btn danger"
            href="/delete/{{s.id}}"
            onclick="return confirm('Delete this student and all marks?')">
            Delete</a>
        </td>
    </tr>
    {% endfor %}
    </table>
    </div>
    </div>
    """

    return show(content, records=records, search=search)


# EDIT STUDENT
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):

    conn = get_db()

    student = conn.execute(
        "SELECT * FROM students WHERE id=?", (id,)
    ).fetchone()

    if not student:
        conn.close()
        return "Student not found", 404

    if request.method == "POST":

        conn.execute("""
            UPDATE students SET
            roll=?,name=?,course=?,contact=?,email=?
            WHERE id=?
        """, (
            request.form["roll"].strip(),
            request.form["name"].strip(),
            request.form["course"],
            request.form["contact"],
            request.form["email"],
            id
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("students"))

    conn.close()

    content = """
    <div class="card">
    <h2>Update Student</h2>

    <form method="POST">
        <label>Roll Number</label>
        <input name="roll" value="{{s.roll}}" required>

        <label>Name</label>
        <input name="name" value="{{s.name}}" required>

        <label>Course</label>
        <input name="course" value="{{s.course}}">

        <label>Contact</label>
        <input name="contact" value="{{s.contact}}">

        <label>Email</label>
        <input name="email" value="{{s.email}}">

        <button>Update Student</button>
    </form>
    </div>
    """

    return show(content, s=student)


# DELETE STUDENT
@app.route("/delete/<int:id>")
def delete_student(id):

    conn = get_db()

    conn.execute("DELETE FROM marks WHERE student_id=?", (id,))
    conn.execute("DELETE FROM students WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect(url_for("students"))


# ADD SUBJECT-WISE MARKS
@app.route("/marks/<int:id>", methods=["GET", "POST"])
def add_marks(id):

    conn = get_db()

    student = conn.execute(
        "SELECT * FROM students WHERE id=?", (id,)
    ).fetchone()

    if not student:
        conn.close()
        return "Student not found", 404

    message = ""

    if request.method == "POST":

        subject = request.form.get("subject", "").strip()

        try:
            obtained = float(request.form["obtained"])
            maximum = float(request.form["maximum"])

            if not subject:
                message = "Enter subject name."
            elif maximum <= 0 or obtained < 0 or obtained > maximum:
                message = "Enter valid marks."
            else:
                conn.execute("""
                    INSERT INTO marks
                    (student_id,subject,obtained,maximum)
                    VALUES(?,?,?,?)
                    ON CONFLICT(student_id,subject)
                    DO UPDATE SET
                    obtained=excluded.obtained,
                    maximum=excluded.maximum
                """, (id,subject,obtained,maximum))

                conn.commit()
                message = "Marks saved successfully!"

        except ValueError:
            message = "Please enter valid numeric marks."

    records = conn.execute(
        "SELECT * FROM marks WHERE student_id=? ORDER BY subject",
        (id,)
    ).fetchall()

    conn.close()

    content = """
    <div class="card">
    <h2>Subject-wise Marks</h2>

    <h3>{{s.name}} ({{s.roll}})</h3>

    {% if message %}
    <div class="notice">{{message}}</div>
    {% endif %}

    <form method="POST">
        <label>Subject Name</label>
        <input name="subject"
        placeholder="Example: Python Programming" required>

        <label>Obtained Marks</label>
        <input type="number" name="obtained"
        min="0" step="any" required>

        <label>Maximum Marks</label>
        <input type="number" name="maximum"
        min="0.01" step="any" value="100" required>

        <button type="submit">Save Marks</button>
    </form>
    </div>

    <div class="card">
    <h3>Saved Subjects and Marks</h3>

    <div class="tablebox">
    <table>
    <tr>
        <th>Subject</th>
        <th>Obtained</th>
        <th>Maximum</th>
    </tr>

    {% for m in records %}
    <tr>
        <td>{{m.subject}}</td>
        <td>{{m.obtained}}</td>
        <td>{{m.maximum}}</td>
    </tr>
    {% endfor %}
    </table>
    </div>

    <p><small>Adding the same subject again updates its marks.</small></p>

    <a class="btn green" href="/result/{{s.id}}">
    View Marksheet</a>

    <a class="btn grey" href="/students">Back</a>
    </div>
    """

    return show(content, s=student, records=records, message=message)


# DELETE SUBJECT MARKS
@app.route("/delete_mark/<int:mark_id>/<int:student_id>")
def delete_mark(mark_id, student_id):

    conn = get_db()

    conn.execute(
        "DELETE FROM marks WHERE id=? AND student_id=?",
        (mark_id,student_id)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("result", id=student_id))


# RESULT AND MARKSHEET
@app.route("/result/<int:id>")
def result(id):

    conn = get_db()

    student = conn.execute(
        "SELECT * FROM students WHERE id=?", (id,)
    ).fetchone()

    conn.close()

    if not student:
        return "Student not found", 404

    records,total,maximum,percentage,grade,status = calculate_result(id)

    content = """
    <div class="card">
    <h2>Student Marksheet</h2>

    <h3>Student Details</h3>

    <p><b>Name:</b> {{s.name}}</p>
    <p><b>Roll Number:</b> {{s.roll}}</p>
    <p><b>Course:</b> {{s.course}}</p>

    <h3>Subject-wise Result</h3>

    <div class="tablebox">
    <table>
    <tr>
        <th>Subject</th>
        <th>Obtained Marks</th>
        <th>Maximum Marks</th>
        <th>Action</th>
    </tr>

    {% for m in records %}
    <tr>
        <td>{{m.subject}}</td>
        <td>{{m.obtained}}</td>
        <td>{{m.maximum}}</td>
        <td>
        <a class="btn danger"
        href="/delete_mark/{{m.id}}/{{s.id}}"
        onclick="return confirm('Delete these marks?')">
        Delete</a>
        </td>
    </tr>
    {% endfor %}
    </table>
    </div>

    <hr>

    <h3>Total Obtained Marks: {{total}}</h3>
    <h3>Maximum Marks: {{maximum}}</h3>
    <h3>Percentage: {{'%.2f'|format(percentage)}}%</h3>
    <h3>Grade: {{grade}}</h3>
    <h3>Final Result: {{status}}</h3>

    <button onclick="window.print()">Print Marksheet</button>

    <a class="btn green" href="/marks/{{s.id}}">
    Add / Update Marks</a>

    <a class="btn grey" href="/students">Back</a>
    </div>
    """

    return show(
        content,
        s=student,
        records=records,
        total=total,
        maximum=maximum,
        percentage=percentage,
        grade=grade,
        status=status
    )


# START APPLICATION
create_table()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
