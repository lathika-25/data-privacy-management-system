from flask import Flask, request, render_template, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"


# ✅ FIXED DB CONNECTION (no lock issues)
def get_db_connection():
    conn = sqlite3.connect("privacy.db", timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def home():
    return redirect("/login")


# ✅ REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


# ✅ LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["user_id"]
            return redirect("/dashboard")
        else:
            return "Invalid Email or Password"

    return render_template("login.html")


# ✅ LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ✅ DASHBOARD
@app.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM requests WHERE user_id=? ORDER BY request_id DESC LIMIT 1",
        (user_id,)
    )
    request_data = cursor.fetchone()

    cursor.execute(
        "SELECT * FROM users WHERE user_id=?",
        (user_id,)
    )
    user = cursor.fetchone()

    conn.close()

    return render_template("dashboard.html", request_data=request_data, user=user)


# ✅ DELETE REQUEST
@app.route("/delete_request", methods=["POST"])
def delete_request():
    user_id = session.get("user_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO requests (user_id, request_type, status) VALUES (?, ?, ?)",
        (user_id, "Delete Account", "Pending")
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ✅ ADMIN PANEL
@app.route("/admin")
def admin():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    cursor.execute("SELECT * FROM requests")
    requests = cursor.fetchall()

    conn.close()

    return render_template("admin.html", users=users, requests=requests)


# ✅ APPROVE
@app.route("/approve_request", methods=["POST"])
def approve():
    request_id = request.form["request_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE requests SET status='Approved' WHERE request_id=?",
        (request_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")


# ✅ REJECT
@app.route("/reject_request", methods=["POST"])
def reject():
    request_id = request.form["request_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE requests SET status='Rejected' WHERE request_id=?",
        (request_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")


# ✅ DELETE USER
@app.route("/delete_user", methods=["POST"])
def delete_user():
    user_id = request.form["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    cursor.execute("DELETE FROM requests WHERE user_id=?", (user_id,))

    conn.commit()
    conn.close()

    return redirect("/admin")


if __name__ == "__main__":
    app.run(debug=True)