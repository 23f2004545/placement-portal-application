from controller.db import db 

class User(db.Model):
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)
    contact = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    blacklisted = db.Column(db.Boolean, default=False)
    image_url = db.Column(db.String(225))
    
    student_details = db.relationship('Student', backref='user', uselist=False)
    company_details = db.relationship('Company', backref='user', uselist=False)
    # user_roles = db.relationship('UserRoles',secondary= , backref='user', lazy=True)
    
class Role(db.Model):
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), nullable=False)
    
    # def __repr__(self):
    #     return f'<User {self.username}>'

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
    
class Company(db.Model):
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    employee_count = db.Column(db.Integer, nullable=False)
    hr_name = db.Column(db.String(80), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    website = db.Column(db.String(225), nullable=False)
    description = db.Column(db.String(700))
    is_approved = db.Column(db.Boolean, default=False)