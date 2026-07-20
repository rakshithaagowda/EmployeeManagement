import sqlite3
import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "employee_secret_key"

DATABASE = "employees.db"
UPLOAD_FOLDER = "static/uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Allowed image extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

# ----------------------------
# Initialize Database
# ----------------------------
def init_db():

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Employee Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            department TEXT NOT NULL,
            designation TEXT NOT NULL,
            salary REAL NOT NULL,
            phone TEXT NOT NULL,
            photo TEXT
        )
    """)

    # Admin Table

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
    """)
    
    # Insert Default Admin
    cursor.execute("""
    INSERT OR IGNORE INTO admin (id, username, password)
    VALUES (1, 'admin', 'admin123')
    """)
    
    conn.commit()
    conn.close()

    # ----------------------------
# Helper Functions
# ----------------------------
def allowed_file(filename):
    return (
        "." in filename and
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def create_upload_folder():
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ----------------------------
# Admin Login
# ----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM admin WHERE username=? AND password=?",
            (username, password)
        )

        admin = cursor.fetchone()

        conn.close()

        if admin:

            session["admin"] = username

            flash("Login Successful!", "success")

            return redirect(url_for("home"))

        else:

            flash("Invalid Username or Password!", "danger")

    return render_template("login.html")
# ----------------------------
# Home Page + Search
# ----------------------------
@app.route("/")
def home():

    search = request.args.get("search", "")

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Dashboard Statistics
    cursor.execute("SELECT COUNT(*) FROM employees")
    total_employees = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT department) FROM employees")
    total_departments = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(salary) FROM employees")
    average_salary = cursor.fetchone()[0]

    if average_salary is None:
        average_salary = 0

    # Employee Search
    if search:
        cursor.execute("""
            SELECT * FROM employees
            WHERE employee_id LIKE ?
               OR full_name LIKE ?
               OR department LIKE ?
               OR designation LIKE ?
            ORDER BY id DESC
        """, (
            f"%{search}%",
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        ))
    else:
        cursor.execute("SELECT * FROM employees ORDER BY id DESC")

    employees = cursor.fetchall()

    conn.close()

    return render_template(
        "index.html",
        employees=employees,
        search=search,
        total_employees=total_employees,
        total_departments=total_departments,
        average_salary=average_salary
    )


# ----------------------------
# Add Employee
# ----------------------------
@app.route("/add", methods=["GET", "POST"])
def add_employee():

    if request.method == "POST":

        employee_id = request.form["employee_id"]
        full_name = request.form["full_name"]
        email = request.form["email"]
        department = request.form["department"]
        designation = request.form["designation"]
        salary = request.form["salary"]
        phone = request.form["phone"]

        # Default photo
        photo_filename = None

        # Check if a photo was uploaded
        photo = request.files.get("photo")

        if photo and photo.filename != "":

            if allowed_file(photo.filename):

                filename = secure_filename(photo.filename)

                # Make filename unique
                photo_filename = f"{employee_id}_{filename}"

                photo.save(
                    os.path.join(
                        app.config["UPLOAD_FOLDER"],
                        photo_filename
                    )
                )

            else:

                flash(
                    "Only JPG, JPEG, PNG and GIF images are allowed.",
                    "danger"
                )

                return redirect(request.url)

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO employees
            (
                employee_id,
                full_name,
                email,
                department,
                designation,
                salary,
                phone,
                photo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            employee_id,
            full_name,
            email,
            department,
            designation,
            salary,
            phone,
            photo_filename
        ))

        conn.commit()
        conn.close()

        flash("Employee Added Successfully!", "success")

        return redirect(url_for("home"))

    return render_template("add_employee.html")


# ----------------------------
# Edit Employee
# ----------------------------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_employee(id):

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get employee details
    cursor.execute("SELECT * FROM employees WHERE id=?", (id,))
    employee = cursor.fetchone()

    if request.method == "POST":

        employee_id = request.form["employee_id"]
        full_name = request.form["full_name"]
        email = request.form["email"]
        department = request.form["department"]
        designation = request.form["designation"]
        salary = request.form["salary"]
        phone = request.form["phone"]

        # Keep existing photo by default
        photo_filename = employee["photo"]

        # Remove current photo
        if request.form.get("delete_photo"):

            if photo_filename:
                photo_path = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    photo_filename
                )

                if os.path.exists(photo_path):
                    os.remove(photo_path)

            photo_filename = None

        # Upload new photo
        photo = request.files.get("photo")

        if photo and photo.filename != "":

            if allowed_file(photo.filename):

                # Delete old photo
                if employee["photo"]:

                    old_photo = os.path.join(
                        app.config["UPLOAD_FOLDER"],
                        employee["photo"]
                    )

                    if os.path.exists(old_photo):
                        os.remove(old_photo)

                filename = secure_filename(photo.filename)

                photo_filename = f"{employee_id}_{filename}"

                photo.save(
                    os.path.join(
                        app.config["UPLOAD_FOLDER"],
                        photo_filename
                    )
                )

            else:

                flash(
                    "Only JPG, JPEG, PNG and GIF images are allowed.",
                    "danger"
                )

                conn.close()

                return redirect(request.url)

        cursor.execute("""
            UPDATE employees
            SET
                employee_id=?,
                full_name=?,
                email=?,
                department=?,
                designation=?,
                salary=?,
                phone=?,
                photo=?
            WHERE id=?
        """, (
            employee_id,
            full_name,
            email,
            department,
            designation,
            salary,
            phone,
            photo_filename,
            id
        ))

        conn.commit()
        conn.close()

        flash("Employee Updated Successfully!", "success")

        return redirect(url_for("home"))

    conn.close()

    return render_template(
        "edit_employee.html",
        employee=employee
    )


# ----------------------------
# Delete Employee
# ----------------------------
@app.route("/delete/<int:id>")
def delete_employee(id):

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM employees WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash("Employee Deleted Successfully!", "danger")

    return redirect(url_for("home"))


# ----------------------------
# Run Application
# ----------------------------
if __name__ == "__main__":
    init_db()
    create_upload_folder()
    app.run(debug=True)