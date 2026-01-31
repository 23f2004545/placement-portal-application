# placement-portal-application
A Placement Portal web application that allows Admin (Institute), Company, and Student to interact with the system based on their roles.

## Admin Seeding & Initialization

### Purpose

This project uses role-based access control (RBAC) with a predefined Admin user.  
Since the Admin is a system-level actor (not created via the user interface), it is created using a dedicated seeding script.

This ensures:
- A default Admin always exists after database initialization
- Admin creation is deterministic and idempotent
- Credentials and roles are not hard-coded into application runtime logic

---

### Why `seed_admin.py` Exists

The `seed_admin.py` script is responsible for:

- Creating the default Admin user
- Assigning the ADMIN role to that user
- Ensuring the operation runs only once per database lifecycle
- Avoiding duplicate admin creation on repeated runs

This logic is intentionally kept outside `app.py` to:

- Prevent accidental reseeding on every application startup
- Maintain a clear separation between runtime logic and setup logic
- Make database initialization explicit and controlled

---

### How to Run the Admin Seeding Script

The script must be executed as a Python module, not as a plain script.

From the project root directory:

```bash
python -m controller.seed_admin 
```

---

### Why `python -m controller.seed_admin` Is Required

This project follows a **package-based structure**, where `controller/` is a Python module inside the application.

If the script is executed like this:

```bash
python controller/seed_admin.py
```
would cause import errors because Python would not recognize the project root as the import base.

Running the script with `-m`:
```bash
python -m controller.seed_admin
```
ensures that:

- Python treats the project root as the module root

- All internal imports (`controller.db`, `controller.models`, `app`) resolve correctly

- The script runs within the same application and database context as the main app

This avoids:

- Duplicate Flask app instances

- Incorrect database bindings

- Import and context-related runtime errors

---

### When to Run the Seeding Script

You should run `seed_admin.py`:

- Once, after the database tables are created

- Again only if the database (`instance/database.sqlite3`) is deleted or reset

You should NOT run it on every application startup.

---

### What Problem This Solves

This approach solves several common issues:

- Ensures a guaranteed Admin account without manual DB manipulation

- Avoids committing database files to version control

- Prevents admin duplication

- Keeps authentication, authorization, and setup logic cleanly separated

- Maintains compatibility with SQLite and Flask’s app context model

---

### Design Note

Admin users are implemented as:

- Entries in the `user` table

- Assigned the `ADMIN` role via the `user_roles` mapping

This allows:

- Support for multiple admins

- Centralized authentication

- Clean role-based authorization without a separate admin table



# here we go 

# Apex - College Placement Portal
**Apex** is a comprehensive, full-stack web application designed to streamline the campus placement process. It serves as a centralized platform connecting **Students**, **Companies**, and the **Placement Cell (Admin)**, facilitating seamless job postings, applications, status tracking, and analytics.

---

## 🚀 Key Features
### 👨‍🎓 For Students
- **Professional Profile** : Build a resume-like profile with skills, experience, and CGPA.
- **Smart Dashboard** : View eligible jobs, application status trends (visualized with Chart.js), and recent activity.
- **One-Click Apply** : Easy application process with duplicate prevention logic.
- **Notification Center** : Real-time updates on applications (Shortlisted/Selected/Rejected) with a "Soft Delete" & "Read/Unread" system.
- **Offer Letter Management** : View, download, and accept/decline job offers digitally.

### 🏢 For Companies
- **Job Management** : Post, edit, and manage job openings with rich descriptions.
- **Application Tracking** : View applicants, filter by status, and shortlist candidates.
- **Status Workflow** : Move candidates through stages (Applied → Shortlisted → Selected) with automated notifications.
- **Analytics** : Visualize application trends per job posting.

### 🛡️ For Admins (Placement Cell)
- **Master Control** : Approve/Reject Company registrations and Job postings to ensure quality.
- **User Management** : Blacklist/Whitelist users and manage platform access.
- **Analytics Dashboard** : High-level insights into total placements, active jobs, and student performance using Charts.
- **Hybrid API** : Built-in REST API endpoints for future mobile integration.

---

## 🛠️ Technology Stack
- **Backend** : Python, Flask (Microframework)
- **Database** : SQLite (SQLAlchemy ORM)
- **Frontend** : HTML5, CSS3, Bootstrap 5 (Glassmorphism UI), JavaScript
- **Authentication** : Flask-Login (Session Management, Role-Based Access Control)
- **Visualization** : Chart.js (Interactive Data Visualization)
- **Security** : Werkzeug Security (Password Hashing), Custom Decorators

---


## 🏗️ Architectural Highlights & Custom Implementations 
We implemented several custom solutions to optimize the user experience beyond standard library features:

1. The "Soft Delete" System
- **Problem** : Deleting a user or job permanently destroys historical data (e.g., a student's past applications).
- **Solution** : Implemented `is_deleted` flags across all models. Data is hidden from the frontend but preserved in the database for integrity and analytics.

2. Finite State Machine for Approvals
- **Problem** : A simple boolean `is_approved` doesn't explain why a company was rejected.
- **Solution** : Used a String Status (`Pending` → `Approved` / `Rejected`) combined with a `rejection_reason` column. This enables a **"Fix & Resubmit"** loop, allowing companies to correct their profiles based on Admin feedback.

3. "Hybrid Lite" API Strategy
- **Problem** : Need to support future mobile apps without rewriting the entire web application.
- **Solution** : Implemented dedicated API blueprints (`/api/v1/...`) alongside standard web routes. This keeps the web logic (HTML rendering) separate from the data logic (JSON serialization), ensuring clean code separation.

4. Custom Decorators (`@company_required`, `@admin_required`)
- **Problem** : Repeating role checks (`if session['role'] == 'company'`) in every route is error-prone.
- **Solution** : Built custom Python decorators that handle Authentication, Role Verification, and "Profile Completeness" checks in a single line of code.

---

## 📂 Project Structure
```bash
BASH 
Placement_Portal_Project/
├── controller/
│   ├── db.py                # Database Initialization
│   ├── decorators.py        # Custom Security Decorators
│   ├── models.py            # Database Schema (User, Student, Job, Application)
│   └── seed_admin.py        # Predifine Admin
├── routes/
│   ├── admin_routes.py      # Approval Workflows & Analytics
│   ├── api_routes.py        # REST API Endpoints (JSON)
│   ├── auth_routes.py       # Login, Register, Logout Logic
│   ├── company_routes.py    # Job Posting & candidate Management
│   ├── main_routes.py       # Main routes ("/" Route | Error handlers etc. )
│   └── student_routes.py    # Student Dashboard & Applications
├── static/
│   ├── css/style.css        # Custom Glassmorphism Styles
│   └── uploads/             # Resumes | Profile Pictures | Offer Letters
├── templates/               # Jinja2 HTML Templates
├── app.py                   # Application Factory & Config
├── config.py                
├── requirements.txt                 
└── README.md                # Project Documentation 
```

---

## ⚙️ Setup & Installation 
**Prerequisites**: Python 3.8+

1. Clone the Repository
```bash
Bash
git clone https://github.com/yourusername/apex-portal.git
cd apex-portal
```

2. Create Virtual Environment
```bash
Bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

3. Install Dependencies
```bash
Bash
pip install -r requirements.txt
```

4. Initialize Database
The app uses `seed_admin.py` (or similar logic) to create the first Admin user.
```bash
Bash
python
>>> from app import db, app
>>> with app.app_context():
>>>     db.create_all()
```

5. Run the Application
```bash
Bash
python app.py
```

- Access the app at `http://127.0.0.1:5000` 

---

## 🧪 API Documentation
The platform includes a lightweight REST API for external integrations.

```markdown
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/jobs` | List all active job postings | Yes |
| `GET` | `/api/students` | List all student profiles | Admin Only |
| `POST` | `/api/application` | Submit a new job application | Student Only |
```
*(All API responses are in JSON format)*

---

## 🤝 Contribution
This project was developed as part of the **IITM BS Degree (MAD-1)** curriculum. It demonstrates proficiency in CRUD operations, Relational Database Design, MVC Architecture, and API Development.
**Developer**: Kartikey Tripathi
**Session**: 2026 - Jan Term