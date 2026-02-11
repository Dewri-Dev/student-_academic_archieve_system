from flask import Flask, render_template, request, redirect, url_for, session
from flask import send_from_directory
import os
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"

@app.route("/subjects")
def subjects():
    if not session.get("is_admin"):
        return "Unauthorized", 403
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM subjects")
    all_subjects = c.fetchall()
    conn.close()
    return render_template("subjects.html", subjects=all_subjects)

@app.route("/subjects/add", methods=["GET", "POST"])
def add_subject():
    if not session.get("is_admin"):
        return "Unauthorized", 403
        
    if request.method == "POST":
        name = request.form.get("name")
        semester = request.form.get("semester")

        if not name or not semester:
            flash("Both subject name and semester are required.", "error")
            return redirect(url_for("add_subject"))

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        # Check if the subject already exists
        c.execute("SELECT id FROM subjects WHERE name = ?", (name,))
        if c.fetchone():
            flash(f"The subject '{name}' already exists.", "error")
        else:
            c.execute("INSERT INTO subjects (name, semester) VALUES (?, ?)", (name, semester))
            conn.commit()
            flash(f"Successfully added subject '{name}'.", "success")
        
        conn.close()
        return redirect(url_for("subjects"))

    return render_template("add_subject.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    student_id = session["user_id"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        SELECT s.name, s.semester, a.attended_classes, a.total_classes
        FROM attendance a
        JOIN subjects s ON a.subject_id = s.id
        WHERE a.student_id = ?
    """, (student_id,))
    attendance_records = c.fetchall()
    conn.close()

    return render_template("dashboard.html", attendance=attendance_records)

# Activity log
def log_action(user_email, action):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO logs (user_email, action, timestamp) VALUES (?, ?, ?)",
              (user_email, action, timestamp))
    conn.commit()
    conn.close()

@app.route("/logs")
def view_logs():
    if not session.get("is_admin"):
        return "Unauthorized", 403

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT user_email, action, timestamp FROM logs ORDER BY id DESC")
    logs = c.fetchall()
    conn.close()
    return render_template("view_logs.html", logs=logs)

# Home page
@app.route("/")
def home():
    return render_template("index.html")

# Login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form["password"]
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        conn.close()
        if user:
            session["user_id"] = user[0]
            session["email"] = email
            session["is_admin"] = bool(user[3])

            # Log the login action
            log_action(email, "Logged In")
            return redirect(url_for("home"))
        else:
            return "Invalid credentials"
    return render_template("login.html")

# Logout page
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# Register page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        if c.fetchone():
            conn.close()
            return "⚠️ Email already registered. Try logging in."

        c.execute("INSERT INTO users (email, password, is_admin) VALUES (?, ?, ?)",
                  (email, password, 0))
        conn.commit()
        # Log the registration action
        log_action(email, "Registered")
        conn.close()
        return redirect("/login")
    
    return render_template("register.html")

# Courses page with search

@app.route("/courses")
def courses():
    # Get the search query from the URL parameters (e.g., /courses?q=python)
    search_query = request.args.get("q", "")
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    
    if search_query:
        # If there is a search query, filter the results using LIKE
        # The '%' are wildcards, so it finds any course containing the query
        c.execute("SELECT * FROM courses WHERE name LIKE ?", ('%' + search_query + '%',))
    else:
        # Otherwise, get all courses
        c.execute("SELECT * FROM courses")
        
    courses = c.fetchall()
    conn.close()
    # Pass the courses and the search query to the template
    return render_template("courses.html", courses=courses, query=search_query)


@app.route("/courses/add", methods=["GET", "POST"])
def add_course():
    if not session.get("is_admin"):
        return redirect(url_for("login"))
    if request.method == "POST":
        name = request.form["name"]
        link = request.form["youtube_link"]
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO courses (name, youtube_link) VALUES (?, ?)", (name, link))
        conn.commit()
        conn.close()
        return redirect(url_for("courses"))
    return render_template("add_course.html")

@app.route("/courses/edit/<int:id>", methods=["GET", "POST"])
def edit_course(id):
    if not session.get("is_admin"):
        return redirect(url_for("login"))
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    if request.method == "POST":
        name = request.form["name"]
        link = request.form["youtube_link"]
        c.execute("UPDATE courses SET name=?, youtube_link=? WHERE id=?", (name, link, id))
        conn.commit()
        conn.close()
        return redirect(url_for("courses"))
    c.execute("SELECT * FROM courses WHERE id=?", (id,))
    course = c.fetchone()
    conn.close()
    return render_template("edit_course.html", course=course)

@app.route("/courses/delete/<int:id>")
def delete_course(id):
    if not session.get("is_admin"):
        return redirect(url_for("login"))
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM courses WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("courses"))

# Question Papers page with search
@app.route("/papers")
def papers():
    # Get the search query from the URL parameters
    search_query = request.args.get("q", "")
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if search_query:
        # If there is a search query, filter by subject, semester, or year
        query_like = '%' + search_query + '%'
        c.execute("""
            SELECT * FROM papers 
            WHERE subject LIKE ? OR semester LIKE ? OR year LIKE ? 
            ORDER BY semester, year, subject
        """, (query_like, query_like, query_like))
    else:
        # Otherwise, get all papers
        c.execute("SELECT * FROM papers ORDER BY semester, year, subject")

    all_papers = c.fetchall()
    conn.close()
    # Pass the papers and the search query to the template
    return render_template("papers.html", papers=all_papers, query=search_query)


@app.route("/papers/add", methods=["GET", "POST"])
def add_paper():
    if not session.get("is_admin"):
        return redirect("/login")
    if request.method == "POST":
        semester = request.form["semester"]
        year = request.form["year"]
        subject = request.form["subject"]
        drive_link = request.form["drive_link"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO papers (semester, year, subject, drive_link) VALUES (?, ?, ?, ?)",
                  (semester, year, subject, drive_link))
        conn.commit()
        conn.close()
        return redirect("/papers")
    return render_template("add_paper.html")

@app.route("/papers/edit/<int:paper_id>", methods=["GET", "POST"])
def edit_paper(paper_id):
    if not session.get("is_admin"):
        return redirect("/login")
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    
    if request.method == "POST":
        semester = request.form["semester"]
        year = request.form["year"]
        subject = request.form["subject"]
        drive_link = request.form["drive_link"]

        c.execute("""
            UPDATE papers
            SET semester=?, year=?, subject=?, drive_link=?
            WHERE id=?
        """, (semester, year, subject, drive_link, paper_id))
        
        conn.commit()
        conn.close()
        return redirect("/papers")

    c.execute("SELECT * FROM papers WHERE id=?", (paper_id,))
    paper = c.fetchone()
    conn.close()
    return render_template("edit_paper.html", paper=paper)

@app.route("/papers/delete/<int:paper_id>")
def delete_paper(paper_id):
    if not session.get("is_admin"):
        return redirect("/login")
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM papers WHERE id=?", (paper_id,))
    conn.commit()
    conn.close()
    return redirect("/papers")

# Admin user viewer
@app.route("/users")
def view_users():
    if not session.get("is_admin"):
        return "Unauthorized", 403

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, email, is_admin FROM users")
    users = c.fetchall()
    conn.close()
    return render_template("view_users.html", users=users)

@app.route("/delete_user/<int:user_id>")
def delete_user(user_id):
    if not session.get("is_admin"):
        return "Unauthorized", 403
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("view_users"))

# NOTES SECTION 
UPLOAD_FOLDER = 'uploads/notes'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Show Notes
@app.route('/notes')
def notes():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, semester, subject, filename, uploader_email FROM notes")
    notes_data = c.fetchall()
    conn.close()
    return render_template('notes.html', notes=notes_data)

@app.route('/notes/add', methods=['GET', 'POST'])
def add_notes():
    # Make sure user is logged in
    if 'email' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        semester = request.form['semester']
        subject = request.form['subject']
        file = request.files['file']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Get uploader's email from session
            uploader_email = session.get('email')

            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            c.execute(
                "INSERT INTO notes (semester, subject, filename, uploader_email) VALUES (?, ?, ?, ?)",
                (semester, subject, filename, uploader_email)
            )
            conn.commit()
            conn.close()

        return redirect(url_for('notes'))

    return render_template('add_notes.html')

@app.route('/notes/delete/<int:note_id>')
def delete_note(note_id):
    if "email" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Get note details
    c.execute("SELECT filename, uploader_email FROM notes WHERE id=?", (note_id,))
    note = c.fetchone()

    if not note:
        conn.close()
        return "Note not found", 404

    filename, uploader_email = note

    # Check permissions: admin or uploader
    if not session.get("is_admin") and session["email"] != uploader_email:
        conn.close()
        return "Unauthorized", 403

    # Delete from database
    c.execute("DELETE FROM notes WHERE id=?", (note_id,))
    conn.commit()
    conn.close()

    # Delete file from server
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    return redirect(url_for("notes"))


# Download Notes
@app.route('/notes/download/<int:note_id>')
def download_notes(note_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT semester, subject, filename FROM notes WHERE id=?", (note_id,))
    note = c.fetchone()
    conn.close()

    if note:
        semester, subject, filename = note
        # Create a nice download name, e.g., Semester1_MathNotes.pdf
        ext = filename.rsplit('.', 1)[1]  # Get file extension
        nice_name = f"Semester{semester}_{subject.replace(' ', '_')}.{ext}"

        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            filename,
            as_attachment=True,
            download_name=nice_name
        )
    return "File not found", 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)