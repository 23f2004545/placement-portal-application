import sys
import os

# Add parent directory to path so imports work when executed directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from controller.db import db
from controller.models import User, Role, Student, Company, JobPosition, Application, Placement
from werkzeug.security import generate_password_hash

def seed_demo_data():
    with app.app_context():
        print("--- Initializing Roles & Demo Accounts ---")
        db.create_all()

        # 1. Ensure Roles
        roles = {}
        for role_name in ['admin', 'company', 'student']:
            r = Role.query.filter_by(name=role_name).first()
            if not r:
                r = Role(name=role_name)
                db.session.add(r)
                db.session.flush()
            roles[role_name] = r
        db.session.commit()

        # 2. Demo Admin
        admin = User.query.filter_by(email="admin@gmail.com").first()
        if not admin:
            admin = User(
                name="Admin Portal",
                email="admin@gmail.com",
                password=generate_password_hash("admin123"),
                contact="9876543210",
                image_url="/static/uploads/Profile_pics/admin.png",
                roles=roles['admin']
            )
            db.session.add(admin)
            print("[+] Demo Admin created: admin@gmail.com / admin123")
        else:
            print("[.] Demo Admin already exists.")

        # 3. Demo Company / Recruiter
        company_user = User.query.filter_by(email="demo_recruiter@company.com").first()
        company_details = None
        if not company_user:
            company_user = User(
                name="Nexus Tech Innovations",
                email="demo_recruiter@company.com",
                password=generate_password_hash("company123"),
                contact="9811223344",
                image_url="/static/uploads/Profile_pics/company.png",
                roles=roles['company']
            )
            db.session.add(company_user)
            db.session.commit()

            company_details = Company(
                user_id=company_user.id,
                hr_name="Sarah Jenkins",
                employee_count=350,
                location="San Francisco, CA",
                website="https://nexustech.example.com",
                description="Next-generation cloud analytics and enterprise software development.",
                status="Approved"
            )
            db.session.add(company_details)
            db.session.commit()

            # Add Demo Job Postings
            job1 = JobPosition(
                company_id=company_details.id,
                job_title="Junior Full-Stack Engineer",
                job_type="Hybrid",
                job_pay="$95,000 / year",
                job_timing="Full Time",
                job_location="San Francisco, CA",
                requirements="Python, Flask/Django, PostgreSQL, React or modern JavaScript.",
                job_description="Join our agile product team building modern web services and dashboards.",
                job_status="Hiring",
                status="Approved"
            )
            job2 = JobPosition(
                company_id=company_details.id,
                job_title="Cloud & DevOps Intern",
                job_type="Remote",
                job_pay="$35 / hour",
                job_timing="Part Time / Internship",
                job_location="Remote",
                requirements="Docker, Linux, CI/CD pipelines, Git, AWS / GCP basics.",
                job_description="Assist in orchestrating containerized microservices and automated deployments.",
                job_status="Hiring",
                status="Approved"
            )
            db.session.add_all([job1, job2])
            db.session.commit()
            print("[+] Demo Company & Job Postings created: demo_recruiter@company.com / company123")
        else:
            company_details = company_user.company_details
            print("[.] Demo Company already exists.")

        # 4. Demo Student
        student_user = User.query.filter_by(email="demo_student@college.edu").first()
        student_details = None
        if not student_user:
            student_user = User(
                name="Alex Morgan",
                email="demo_student@college.edu",
                password=generate_password_hash("student123"),
                contact="9123456789",
                image_url="/static/uploads/Profile_pics/student.png",
                roles=roles['student']
            )
            db.session.add(student_user)
            db.session.commit()

            student_details = Student(
                user_id=student_user.id,
                cgpa=8.9,
                experience=1,
                skill_set="Python, Flask, PostgreSQL, Docker, Git, REST APIs",
                resume="/static/uploads/Resumes/demo_resume.pdf",
                milestones="Finalist at National Hackathon 2025; Dean's Honor List."
            )
            db.session.add(student_details)
            db.session.commit()
            print("[+] Demo Student created: demo_student@college.edu / student123")
        else:
            student_details = student_user.student_details
            print("[.] Demo Student already exists.")

        # 5. Link a sample application and placement offer if jobs exist
        if company_details and student_details:
            first_job = JobPosition.query.filter_by(company_id=company_details.id).first()
            if first_job:
                existing_app = Application.query.filter_by(student_id=student_details.id, job_position_id=first_job.id).first()
                if not existing_app:
                    demo_app = Application(
                        student_id=student_details.id,
                        job_position_id=first_job.id,
                        application_status='Selected',
                        cover_letter="I am very excited about Nexus Tech Innovations and would love to contribute my full-stack skills.",
                        remarks="Outstanding interview performance and technical problem solving."
                    )
                    db.session.add(demo_app)
                    db.session.commit()

                    demo_placement = Placement(
                        application_id=demo_app.id,
                        salary_offered="$95,000 / year",
                        joining_date="July 1, 2026",
                        offer_letter="/static/uploads/Offer_letters/demo_offer.pdf",
                        status="Offered"
                    )
                    db.session.add(demo_placement)
                    db.session.commit()
                    print("[+] Demo Application & Job Offer created.")

        db.session.commit()
        print("--- Demo Seeding Completed Successfully! ---")

if __name__ == "__main__":
    seed_demo_data()
