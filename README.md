# Employee Management System

A modern **Employee Management System** built with **Flask** and **SQLite** that enables administrators to efficiently manage employee records through a secure and intuitive web interface.

## 🚀 Features

### Employee Management
- Add new employees
- Edit employee details
- Delete employees
- View all employee records
- Employee photo upload
- Search employees by:
  - Employee ID
  - Name
  - Department
  - Designation

### Authentication & Security
- Admin login
- Password hashing
- Protected routes
- Secure password change
- Session-based authentication
- Logout functionality

### Dashboard
- Total employees
- Total departments
- Average salary
- Dashboard analytics
- Department pie chart

### Reports
- Employee summary
- Department summary
- Average salary analysis
- Total salary statistics
- Department analytics

### Export
- Export employee data to Excel (.xlsx)

---

## 🛠 Tech Stack

### Backend
- Flask
- Python

### Frontend
- HTML5
- CSS3
- Bootstrap 5
- Jinja2
- JavaScript
- Chart.js

### Database
- SQLite

### Libraries
- OpenPyXL
- Werkzeug

---

## 📂 Project Structure

```
EmployeeManagement/
│
├── static/
│   ├── css/
│   └── uploads/
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── add_employee.html
│   ├── edit_employee.html
│   ├── login.html
│   ├── change_password.html
│   └── reports.html
│
├── app.py
├── employees.db
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

### Clone the repository

```bash
git clone https://github.com/rakshithaagowda/EmployeeManagement.git
```

### Navigate to the project

```bash
cd EmployeeManagement
```

### Create a virtual environment

```bash
python -m venv venv
```

### Activate the virtual environment

Windows

```bash
venv\Scripts\activate
```

Linux / macOS

```bash
source venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the application

```bash
python app.py
```

Visit:

```
http://127.0.0.1:5000
```
---

## 📈 Future Enhancements

- PDF Export
- Email Notifications
- Role-based Access Control
- Employee Attendance Module
- Payroll Management
- REST API
- Cloud Database Support

---

## 👩‍💻 Author

Rakshitha R S

GitHub:
https://github.com/rakshithaagowda

---

## ⭐ Support

If you like this project, consider giving it a ⭐ on GitHub.
