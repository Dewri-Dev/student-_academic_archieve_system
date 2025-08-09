from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "your_secret_key"

#last seen update
def update_last_seen(username):
    conn = sqlite3.connect('database')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET last_seen = ? WHERE username = ?", 
                   (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), username))
    conn.commit()
    conn.close()

@app.before_request
def track_user_activity():
    from flask import session
    if 'username' in session:
        update_last_seen(session['username'])

def is_online(last_seen):
    if not last_seen:
        return False
    last_seen_time = datetime.strptime(last_seen, '%Y-%m-%d %H:%M:%S')
    return (datetime.now() - last_seen_time).seconds < 300


#remove the ngork header
@app.after_request
def add_ngrok_header(response):
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response

#activity log
from datetime import datetime

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



@app.route('/view_users')
def users_simple_status():
    conn = sqlite3.connect('database')
    cursor = conn.cursor()
    cursor.execute("SELECT username, last_seen FROM users")
    users_data = cursor.fetchall()
    conn.close()

    users_status = [(u, "Online" if is_online(ls) else "Offline") for u, ls in users_data]
    return render_template("view_users.html", users=users_status)




#home page aitu
@app.route("/")
def home():
    return render_template("index.html")

#login page aitu
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
            session["is_admin"] = bool(user[3])
            return redirect(url_for("home"))
        else:
            return "Invalid credentials"
    return render_template("login.html")

#logout page
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

#register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        # Check if user already exists
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        if c.fetchone():
            conn.close()
            return "⚠️ Email already registered. Try logging in."

        # Register as normal user (is_admin = 0)
        c.execute("INSERT INTO users (email, password, is_admin) VALUES (?, ?, ?)",
                  (email, password, 0))

        conn.commit()
        conn.close()
        return redirect("/login")
    
    return render_template("register.html")



#courses
@app.route("/courses")
def courses():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM courses")
    courses = c.fetchall()
    conn.close()
    return render_template("courses.html", courses=courses)

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

# Question Papers
@app.route("/papers")
def papers():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM papers ORDER BY semester, year, subject")
    all_papers = c.fetchall()
    conn.close()
    return render_template("papers.html", papers=all_papers)


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

    # If GET, load existing data
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
#admin viewer
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
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("view_users"))



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

