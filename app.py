import sqlite3
import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_file
)

from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from openpyxl import Workbook

app = Flask(__name__)
app.secret_key = "employee_secret_key"

DATABASE = "employees.db"
UPLOAD_FOLDER = "static/uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Allowed image extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
# ----------------------------
# Login Required
# ----------------------------
def login_required():

    if "admin" not in session:
        return False

    return True

# ----------------------------
# Logout
# ----------------------------
@app.route("/logout")
def logout():

    session.pop("admin", None)

    flash("Logged out successfully!", "success")

    return redirect(url_for("login"))

# ----------------------------
# Change Password
# ----------------------------
@app.route("/change-password", methods=["GET", "POST"])
def change_password():

    if "admin" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM admin WHERE username=?",
            (session["admin"],)
        )

        admin = cursor.fetchone()

        # Check current password
        if not check_password_hash(admin["password"], current_password):

            flash("Current password is incorrect!", "danger")
            conn.close()
            return redirect(url_for("change_password"))

        # Check new passwords match
        if new_password != confirm_password:

            flash("New passwords do not match!", "warning")
            conn.close()
            return redirect(url_for("change_password"))

        # Hash the new password
        hashed_password = generate_password_hash(new_password)

        cursor.execute(
            "UPDATE admin SET password=? WHERE username=?",
            (hashed_password, session["admin"])
        )

        conn.commit()
        conn.close()

        flash("Password changed successfully!", "success")

        return redirect(url_for("home"))

    return render_template("change_password.html")
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
    hashed_password = generate_password_hash("admin123")

    cursor.execute("""
    INSERT OR IGNORE INTO admin (id, username, password)
    VALUES (?, ?, ?)
    """, (
    1,
    "admin",
    hashed_password
))
    
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
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM admin WHERE username=?",
            (username,)
        )

        admin = cursor.fetchone()

        conn.close()

        if admin and check_password_hash(admin["password"], password):

            session["admin"] = admin["username"]

            flash("Login Successful!", "success")

            return redirect(url_for("home"))

        flash("Invalid Username or Password!", "danger")

    return render_template("login.html")
# ----------------------------
# Home Page + Search
# ----------------------------
@app.route("/")
def home():
    if not login_required():
        return redirect(url_for("login"))
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

    # Employees by Department
    cursor.execute("""
    SELECT department, COUNT(*) as total
    FROM employees
    GROUP BY department
    """)

    department_data = cursor.fetchall()

    # Salary by Employee
    cursor.execute("""
    SELECT full_name, salary
    FROM employees
    ORDER BY salary DESC
    """)

    salary_data = cursor.fetchall()

    conn.close()

    return render_template(
    "index.html",
    employees=employees,
    search=search,
    total_employees=total_employees,
    total_departments=total_departments,
    average_salary=average_salary,
    department_data=department_data,
    salary_data=salary_data
)


# ----------------------------
# Add Employee
# ----------------------------
@app.route("/add", methods=["GET", "POST"])
def add_employee():
    if not login_required():
        return redirect(url_for("login"))
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
    if not login_required():
        return redirect(url_for("login"))
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
    if not login_required():
        return redirect(url_for("login"))

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
# Export Employees to Excel
# ----------------------------
@app.route("/export/excel")
def export_excel():

    if "admin" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            employee_id,
            full_name,
            email,
            department,
            designation,
            salary,
            phone
        FROM employees
        ORDER BY employee_id
    """)

    employees = cursor.fetchall()
    conn.close()

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Employees"

    # Header Row
    sheet.append([
        "Employee ID",
        "Full Name",
        "Email",
        "Department",
        "Designation",
        "Salary",
        "Phone"
    ])

    # Employee Data
    for employee in employees:
        sheet.append([
            employee["employee_id"],
            employee["full_name"],
            employee["email"],
            employee["department"],
            employee["designation"],
            employee["salary"],
            employee["phone"]
        ])

    filename = os.path.join(os.getcwd(), "employees.xlsx")
    workbook.save(filename)

    return send_file(
        filename,
        as_attachment=True,
        download_name="employees.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

# ----------------------------
# Reports
# ----------------------------
@app.route("/reports")
def reports():

    if "admin" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Summary Statistics
    cursor.execute("SELECT COUNT(*) FROM employees")
    total_employees = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT department) FROM employees")
    total_departments = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(salary) FROM employees")
    average_salary = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(salary) FROM employees")
    total_salary = cursor.fetchone()[0] or 0

    # Department Report
    cursor.execute("""
        SELECT department,
               COUNT(*) AS total
        FROM employees
        GROUP BY department
    """)
    department_data = cursor.fetchall()

    conn.close()

    return render_template(
        "reports.html",
        total_employees=total_employees,
        total_departments=total_departments,
        average_salary=average_salary,
        total_salary=total_salary,
        department_data=department_data
    )
# ----------------------------
# Run Application
# ----------------------------
if __name__ == "__main__":
    init_db()
    create_upload_folder()
    app.run(debug=True)