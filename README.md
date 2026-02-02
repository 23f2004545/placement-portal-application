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

**1. The "Soft Delete" System**
- **Problem** : Deleting a user or job permanently destroys historical data (e.g., a student's past applications).
- **Solution** : Implemented `is_deleted` flags across all models. Data is hidden from the frontend but preserved in the database for integrity and analytics.

**2. Finite State Machine for Approvals**
- **Problem** : A simple boolean `is_approved` doesn't explain why a company was rejected.
- **Solution** : Used a String Status (`Pending` → `Approved` / `Rejected`) combined with a `rejection_reason` column. This enables a **"Fix & Resubmit"** loop, allowing companies to correct their profiles based on Admin feedback.

**3. "Hybrid Lite" API Strategy**
- **Problem** : Need to support future mobile apps without rewriting the entire web application.
- **Solution** : Implemented dedicated API blueprints (`/api/v1/...`) alongside standard web routes. This keeps the web logic (HTML rendering) separate from the data logic (JSON serialization), ensuring clean code separation.

**4. Custom Decorators (`@company_required`, `@admin_required`)**
- **Problem** : Repeating role checks (`if session['role'] == 'company'`) in every route is error-prone.
- **Solution** : Built custom Python decorators that handle Authentication, Role Verification, and "Profile Completeness" checks in a single line of code.

---

## 📂 Project Structure
```bash
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

**1. Clone the Repository**
```bash
git clone https://github.com/23f2004545/placement-portal-application.git
cd apex-portal
```

**2. Create Virtual Environment**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

**3. Install Dependencies**
```bash
pip install -r requirements.txt
```

**4. Initialize Database**
The app uses `seed_admin.py` (or similar logic) to create the first Admin user.
```bash
python
>>> from app import db, app
>>> with app.app_context():
>>>     db.create_all()
```

**5. Run the Application**
```bash
python app.py
```

- Access the app at `http://127.0.0.1:5000` 

---

## 🧪 API Documentation
The platform includes a lightweight REST API for external integrations.

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/companies` | List all company profiles | Yes |
| `GET` | `/api/students` | List all student profiles | Admin Only |
| `POST` | `/api/application` | Submit a new job application | Student Only |

*(All API responses are in JSON format)*

---

## 🤝 Contribution
This project was developed as part of the **IITM BS Degree (MAD-1)** curriculum. It demonstrates proficiency in CRUD operations, Relational Database Design, MVC Architecture, and API Development.  
**Developer**: Kartikey Tripathi  
**Session**: 2026 - Jan Term  