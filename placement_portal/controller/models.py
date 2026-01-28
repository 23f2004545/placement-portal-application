from controller.db import db 
import secrets

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)
    contact = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    
    # --- NEW: Security & Analytics ---
    # fs_uniquifier: Critical for Flask-Security (invalidates old cookies on password change)
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False, default=secrets.token_urlsafe(16))
    last_login_at = db.Column(db.DateTime) 
    
    # Status
    blacklisted = db.Column(db.Boolean, default=False)
    image_url = db.Column(db.String(225)) 
    
    # Relationships
    student_details = db.relationship('Student', backref='user', lazy=True, uselist=False)
    company_details = db.relationship('Company', backref='user', lazy=True, uselist=False)
    roles = db.relationship('Role', secondary='user_roles', backref='user', lazy=True, uselist=False)

    @property
    def is_active(self):
        return not self.blacklisted

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(10), nullable=False)

class UserRoles(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cgpa = db.Column(db.Float, nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    skill_set = db.Column(db.String(200), nullable=False)
    resume = db.Column(db.String(225), nullable=False)
    milestones = db.Column(db.String(500))
    
    # --- NEW: Soft Delete ---
    is_deleted = db.Column(db.Boolean, default=False) 
    
    applications = db.relationship('Application', backref='student', lazy=True)

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    employee_count = db.Column(db.Integer, nullable=False)
    hr_name = db.Column(db.String(80), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    website = db.Column(db.String(225), nullable=False)
    description = db.Column(db.String(700))
    
    # --- CHANGED: Approval Logic (String Status) ---
    # We replaced 'is_approved' with 'status' and 'rejection_reason'
    status = db.Column(db.String(20), default='Pending') # 'Pending', 'Approved', 'Rejected'
    rejection_reason = db.Column(db.String(255)) 
    
    # --- NEW: Soft Delete ---
    is_deleted = db.Column(db.Boolean, default=False)
    
    job_postings = db.relationship('JobPosition', backref='company', lazy=True)

class JobPosition(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    requirements = db.Column(db.String(200), nullable=False)
    job_location = db.Column(db.String(200), nullable=False)
    job_description = db.Column(db.String(700))
    job_title = db.Column(db.String(100), nullable=False)
    job_pay = db.Column(db.String(40), nullable=False)
    job_type = db.Column(db.String(7), nullable=False) # Remote , Onsite , Hybrid 
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    job_status = db.Column(db.String(10), default='Hiring') # Hiring , Closed
    
    # --- CHANGED: Approval & Status Logic ---
    status = db.Column(db.String(20), default='Pending') # 'Pending', 'Approved', 'Rejected', 'Closed'
    rejection_reason = db.Column(db.String(255))
    
    job_timing = db.Column(db.String(30), nullable=False)
    
    # --- NEW: Analytics & Soft Delete ---
    views = db.Column(db.Integer, default=0) 
    is_deleted = db.Column(db.Boolean, default=False) 

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    job_position_id = db.Column(db.Integer, db.ForeignKey('job_position.id'), nullable=False)
    application_status = db.Column(db.String(15), default='Applied') # Applied , Reviewed , Interviewed , Selected , Rejected
    applied_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    cover_letter = db.Column(db.String(250))
    custom_resume = db.Column(db.String(225))
    
    # --- NEW: Notifications & Feedback ---
    remarks = db.Column(db.String(500)) # Recruiter feedback
    is_read = db.Column(db.Boolean, default=False)
    is_cleared = db.Column(db.Boolean, default=False)
    
    placements = db.relationship('Placement', backref='application', lazy=True, uselist=False)
    job_position = db.relationship('JobPosition', backref='applications', lazy=True)

class Placement(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp()) 
    salary_offered = db.Column(db.String(40), nullable=False)
    joining_date = db.Column(db.String(20), nullable=False) # when the student is expected to join
    offer_letter = db.Column(db.String(225), nullable=False)
    status = db.Column(db.String(15), default='Offered') # Offered , Joined , Declined