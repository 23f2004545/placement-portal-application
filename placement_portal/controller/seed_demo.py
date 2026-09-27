import sys
import os

# Add parent directory to path so imports work when executed directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controller.db import db
from controller.models import User, Role, Student, Company, JobPosition, Application, Placement
from werkzeug.security import generate_password_hash

DEMO_ACCOUNTS = {
    'admin': 'admin@portfolio.demo',
    'company': 'company@portfolio.demo',
    'recruiter': 'company@portfolio.demo',
    'student': 'student@portfolio.demo'
}

def ensure_demo_dataset():
    """
    Dynamically seeds or verifies the resilient baseline dataset.
    Ensures:
      - 3 core roles (admin, company, student)
      - Demo admin (admin@portfolio.demo)
      - 2 Demo companies (company@portfolio.demo, cloudscale@portfolio.demo)
      - 2 Demo job postings (Junior Full-Stack Engineer, Cloud & DevOps Intern)
      - 2 Demo students (student@portfolio.demo, student2@portfolio.demo)
      - 2 Demo applications linked between them (one Selected with Placement offer, one Reviewed)
    Never alters or deletes real registered users (emails not ending in @portfolio.demo).
    """
    # 1. Ensure Roles
    roles = {}
    for role_name in ['admin', 'company', 'student']:
        r = Role.query.filter_by(name=role_name).first()
        if not r:
            r = Role(name=role_name)
            db.session.add(r)
            db.session.flush()
        roles[role_name] = r

    # 2. Demo Admin
    admin_email = "admin@portfolio.demo"
    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        admin = User(
            name="Portfolio Admin (Demo)",
            email=admin_email,
            password=generate_password_hash("admin123"),
            contact="9876543210",
            image_url="/static/uploads/Profile_pics/admin.png",
            roles=roles['admin']
        )
        db.session.add(admin)
        db.session.flush()
    else:
        admin.name = "Portfolio Admin (Demo)"
        if admin.blacklisted:
            admin.blacklisted = False

    # 3. Demo Companies (2 sample companies)
    # Company 1 (Primary Demo Recruiter)
    comp1_email = "company@portfolio.demo"
    comp1_user = User.query.filter_by(email=comp1_email).first()
    if not comp1_user:
        comp1_user = User(
            name="Nexus Tech Innovations (Demo)",
            email=comp1_email,
            password=generate_password_hash("company123"),
            contact="9811223344",
            image_url="/static/uploads/Profile_pics/company.png",
            roles=roles['company']
        )
        db.session.add(comp1_user)
        db.session.flush()

        comp1 = Company(
            user_id=comp1_user.id,
            hr_name="Sarah Jenkins",
            employee_count=350,
            location="San Francisco, CA",
            website="https://nexustech.example.com",
            description="Next-generation cloud analytics and enterprise software development.",
            status="Approved",
            is_deleted=False
        )
        db.session.add(comp1)
        db.session.flush()
    else:
        comp1_user.name = "Nexus Tech Innovations (Demo)"
        comp1_user.blacklisted = False
        comp1 = comp1_user.company_details
        if comp1:
            comp1.is_deleted = False
            comp1.status = "Approved"
        else:
            comp1 = Company(
                user_id=comp1_user.id,
                hr_name="Sarah Jenkins",
                employee_count=350,
                location="San Francisco, CA",
                website="https://nexustech.example.com",
                description="Next-generation cloud analytics and enterprise software development.",
                status="Approved",
                is_deleted=False
            )
            db.session.add(comp1)
            db.session.flush()

    # Company 2 (Secondary Demo Company)
    comp2_email = "cloudscale@portfolio.demo"
    comp2_user = User.query.filter_by(email=comp2_email).first()
    if not comp2_user:
        comp2_user = User(
            name="CloudScale AI Labs (Demo)",
            email=comp2_email,
            password=generate_password_hash("company123"),
            contact="9822334455",
            image_url="/static/uploads/Profile_pics/company.png",
            roles=roles['company']
        )
        db.session.add(comp2_user)
        db.session.flush()

        comp2 = Company(
            user_id=comp2_user.id,
            hr_name="David Chen",
            employee_count=120,
            location="Austin, TX",
            website="https://cloudscale.example.com",
            description="Scalable machine learning infrastructure and distributed backend systems.",
            status="Approved",
            is_deleted=False
        )
        db.session.add(comp2)
        db.session.flush()
    else:
        comp2_user.name = "CloudScale AI Labs (Demo)"
        comp2_user.blacklisted = False
        comp2 = comp2_user.company_details
        if comp2:
            comp2.is_deleted = False
            comp2.status = "Approved"
        else:
            comp2 = Company(
                user_id=comp2_user.id,
                hr_name="David Chen",
                employee_count=120,
                location="Austin, TX",
                website="https://cloudscale.example.com",
                description="Scalable machine learning infrastructure and distributed backend systems.",
                status="Approved",
                is_deleted=False
            )
            db.session.add(comp2)
            db.session.flush()

    # 4. Demo Jobs (2 sample job postings)
    # Job 1 under Company 1
    job1 = JobPosition.query.filter_by(company_id=comp1.id, job_title="Junior Full-Stack Engineer").first()
    if not job1:
        job1 = JobPosition(
            company_id=comp1.id,
            job_title="Junior Full-Stack Engineer",
            job_type="Hybrid",
            job_pay="$95,000 / year",
            job_timing="Full Time",
            job_location="San Francisco, CA",
            requirements="Python, Flask, PostgreSQL, React, Git fundamentals.",
            job_description="Join our agile product team building modern web services and dashboards.",
            job_status="Hiring",
            status="Approved",
            is_deleted=False
        )
        db.session.add(job1)
        db.session.flush()
    else:
        job1.is_deleted = False
        job1.status = "Approved"
        job1.job_status = "Hiring"

    # Job 2 under Company 2
    job2 = JobPosition.query.filter_by(company_id=comp2.id, job_title="Cloud & DevOps Intern").first()
    if not job2:
        job2 = JobPosition(
            company_id=comp2.id,
            job_title="Cloud & DevOps Intern",
            job_type="Remote",
            job_pay="$35 / hour",
            job_timing="Part Time / Internship",
            job_location="Remote",
            requirements="Docker, Linux, CI/CD pipelines, Git, AWS / GCP basics.",
            job_description="Assist in orchestrating containerized microservices and automated deployments.",
            job_status="Hiring",
            status="Approved",
            is_deleted=False
        )
        db.session.add(job2)
        db.session.flush()
    else:
        job2.is_deleted = False
        job2.status = "Approved"
        job2.job_status = "Hiring"

    # 5. Demo Students (2 sample student profiles)
    # Student 1 (Primary Demo Student)
    stud1_email = "student@portfolio.demo"
    stud1_user = User.query.filter_by(email=stud1_email).first()
    if not stud1_user:
        stud1_user = User(
            name="Alex Morgan (Demo)",
            email=stud1_email,
            password=generate_password_hash("student123"),
            contact="9123456789",
            image_url="/static/uploads/Profile_pics/student.png",
            roles=roles['student']
        )
        db.session.add(stud1_user)
        db.session.flush()

        stud1 = Student(
            user_id=stud1_user.id,
            cgpa=8.9,
            experience=1,
            skill_set="Python, Flask, PostgreSQL, Docker, Git, REST APIs",
            resume="/static/uploads/Resumes/demo_resume.pdf",
            milestones="Finalist at National Hackathon 2025; Dean's Honor List.",
            is_deleted=False
        )
        db.session.add(stud1)
        db.session.flush()
    else:
        stud1_user.name = "Alex Morgan (Demo)"
        stud1_user.blacklisted = False
        stud1 = stud1_user.student_details
        if stud1:
            stud1.is_deleted = False
        else:
            stud1 = Student(
                user_id=stud1_user.id,
                cgpa=8.9,
                experience=1,
                skill_set="Python, Flask, PostgreSQL, Docker, Git, REST APIs",
                resume="/static/uploads/Resumes/demo_resume.pdf",
                milestones="Finalist at National Hackathon 2025; Dean's Honor List.",
                is_deleted=False
            )
            db.session.add(stud1)
            db.session.flush()

    # Student 2 (Secondary Demo Student)
    stud2_email = "student2@portfolio.demo"
    stud2_user = User.query.filter_by(email=stud2_email).first()
    if not stud2_user:
        stud2_user = User(
            name="Priya Sharma (Demo)",
            email=stud2_email,
            password=generate_password_hash("student123"),
            contact="9123456780",
            image_url="/static/uploads/Profile_pics/student.png",
            roles=roles['student']
        )
        db.session.add(stud2_user)
        db.session.flush()

        stud2 = Student(
            user_id=stud2_user.id,
            cgpa=9.2,
            experience=2,
            skill_set="Python, Machine Learning, PyTorch, SQL, FastAPI",
            resume="/static/uploads/Resumes/demo_resume.pdf",
            milestones="Published undergraduate paper on ML; Open source contributor.",
            is_deleted=False
        )
        db.session.add(stud2)
        db.session.flush()
    else:
        stud2_user.name = "Priya Sharma (Demo)"
        stud2_user.blacklisted = False
        stud2 = stud2_user.student_details
        if stud2:
            stud2.is_deleted = False
        else:
            stud2 = Student(
                user_id=stud2_user.id,
                cgpa=9.2,
                experience=2,
                skill_set="Python, Machine Learning, PyTorch, SQL, FastAPI",
                resume="/static/uploads/Resumes/demo_resume.pdf",
                milestones="Published undergraduate paper on ML; Open source contributor.",
                is_deleted=False
            )
            db.session.add(stud2)
            db.session.flush()

    # 6. Demo Applications (2 sample applications linked between them)
    # Application 1: Student 1 -> Job 1 (Selected + Placement Offer)
    app1 = Application.query.filter_by(student_id=stud1.id, job_position_id=job1.id).first()
    if not app1:
        app1 = Application(
            student_id=stud1.id,
            job_position_id=job1.id,
            application_status='Selected',
            cover_letter="I am very excited about Nexus Tech Innovations and would love to contribute my full-stack skills.",
            remarks="Outstanding interview performance and technical problem solving."
        )
        db.session.add(app1)
        db.session.flush()

        placement1 = Placement(
            application_id=app1.id,
            salary_offered="$95,000 / year",
            joining_date="July 1, 2026",
            offer_letter="/static/uploads/Offer_letters/demo_offer.pdf",
            status="Offered"
        )
        db.session.add(placement1)
        db.session.flush()
    else:
        if not app1.placements:
            placement1 = Placement(
                application_id=app1.id,
                salary_offered="$95,000 / year",
                joining_date="July 1, 2026",
                offer_letter="/static/uploads/Offer_letters/demo_offer.pdf",
                status="Offered"
            )
            db.session.add(placement1)
            db.session.flush()

    # Application 2: Student 2 -> Job 2 (Reviewed)
    app2 = Application.query.filter_by(student_id=stud2.id, job_position_id=job2.id).first()
    if not app2:
        app2 = Application(
            student_id=stud2.id,
            job_position_id=job2.id,
            application_status='Reviewed',
            cover_letter="Passionate about scalable cloud infrastructure and container technologies.",
            remarks="Resume shortlisted for technical interview round."
        )
        db.session.add(app2)
        db.session.flush()

    db.session.commit()
    return {
        'admin': admin,
        'company': comp1_user,
        'student': stud1_user
    }

def seed_demo_data():
    from app import app
    with app.app_context():
        print("--- Seeding Resilient Demo Dataset ---")
        db.create_all()
        ensure_demo_dataset()
        print("--- Demo Seeding Completed Successfully! ---")

if __name__ == "__main__":
    seed_demo_data()
