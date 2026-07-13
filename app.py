import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "employee_secret_key"

DATABASE = "employees.db"


# ----------------------------
# Initialize Database
# ----------------------------
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

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

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO employees
            (employee_id, full_name, email, department, designation, salary, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            employee_id,
            full_name,
            email,
            department,
            designation,
            salary,
            phone
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

    if request.method == "POST":

        employee_id = request.form["employee_id"]
        full_name = request.form["full_name"]
        email = request.form["email"]
        department = request.form["department"]
        designation = request.form["designation"]
        salary = request.form["salary"]
        phone = request.form["phone"]

        cursor.execute("""
            UPDATE employees
            SET
                employee_id=?,
                full_name=?,
                email=?,
                department=?,
                designation=?,
                salary=?,
                phone=?
            WHERE id=?
        """, (
            employee_id,
            full_name,
            email,
            department,
            designation,
            salary,
            phone,
            id
        ))

        conn.commit()
        conn.close()

        flash("Employee Updated Successfully!", "success")

        return redirect(url_for("home"))

    cursor.execute(
        "SELECT * FROM employees WHERE id=?",
        (id,)
    )

    employee = cursor.fetchone()

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
    app.run(debug=True)