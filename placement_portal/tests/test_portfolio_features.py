import os
import sys
import unittest

# Ensure app is on Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from controller.db import db
from controller.models import User, Role, Student, Company, JobPosition, Application, Placement
from controller.storage import upload_file
from io import BytesIO

class TestPlacementPortal(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['CLOUDINARY_URL'] = None
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_01_demo_logins(self):
        """Test one-click demo login for Admin, Recruiter, and Student."""
        # 1. Admin Demo Login
        res_admin = self.client.get('/auth/demo-login/admin', follow_redirects=True)
        self.assertEqual(res_admin.status_code, 200)
        self.assertIn(b"Logged in as Demo Admin", res_admin.data)
        self.client.get('/auth/logout')

        # 2. Company Demo Login
        res_comp = self.client.get('/auth/demo-login/company', follow_redirects=True)
        self.assertEqual(res_comp.status_code, 200)
        self.assertIn(b"Logged in as Demo Company", res_comp.data)
        self.client.get('/auth/logout')

        # 3. Student Demo Login
        res_stud = self.client.get('/auth/demo-login/student', follow_redirects=True)
        self.assertEqual(res_stud.status_code, 200)
        self.assertIn(b"Logged in as Demo Student", res_stud.data)
        self.client.get('/auth/logout')

        # 4. Invalid Role Demo Login
        res_inv = self.client.get('/auth/demo-login/unknown_role', follow_redirects=True)
        self.assertIn(b"Invalid demo role selected", res_inv.data)

    def test_02_model_fs_uniquifier_dynamic_generation(self):
        """Verify that fs_uniquifier generates unique tokens per user row."""
        role_stud = Role.query.filter_by(name='student').first()
        u1 = User(name="User One", email="unique1@test.com", password="pw", contact="1111111111", roles=role_stud)
        u2 = User(name="User Two", email="unique2@test.com", password="pw", contact="2222222222", roles=role_stud)
        
        db.session.add_all([u1, u2])
        db.session.commit()
        
        self.assertNotEqual(u1.fs_uniquifier, u2.fs_uniquifier)
        
        # Clean up
        db.session.delete(u1)
        db.session.delete(u2)
        db.session.commit()

    def test_03_notification_context_processor_no_crash_on_new_student(self):
        """Verify newly registered student without student_details does NOT crash page rendering."""
        role_stud = Role.query.filter_by(name='student').first()
        new_stud = User(name="Incomplete Setup Student", email="incomplete@test.com", password="pw", contact="3333333333", roles=role_stud)
        db.session.add(new_stud)
        db.session.commit()

        # Log in as this new student
        with self.client:
            self.client.get(f'/auth/demo-login/student')
            # Now simulate logged in as new_stud
            from flask_login import login_user
            with self.client.session_transaction() as sess:
                sess['_user_id'] = str(new_stud.id)

            # Request page that evaluates context_processor
            res = self.client.get('/auth/login')
            self.assertEqual(res.status_code, 302) # redirects to student_bp.profile without crashing
            
            # Clean up
            db.session.delete(new_stud)
            db.session.commit()

    def test_04_storage_local_fallback(self):
        """Test file storage local fallback generates valid URLs and writes to disk."""
        dummy_file = BytesIO(b"%PDF-1.4 dummy pdf content")
        dummy_file.filename = "sample_resume.pdf"
        
        url = upload_file(dummy_file, folder_name="TestResumes")
        self.assertIsNotNone(url)
        self.assertTrue(url.startswith("/static/uploads/TestResumes/"))
        self.assertTrue(url.endswith("sample_resume.pdf"))

    def test_05_admin_dashboard_render(self):
        """Verify Admin dashboard renders without database error."""
        self.client.get('/auth/demo-login/admin')
        res = self.client.get('/admin/profile')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Companies", res.data)
        self.assertIn(b"Students", res.data)
        self.client.get('/auth/logout')

    def test_06_company_dashboard_render(self):
        """Verify Company recruiter dashboard renders cleanly."""
        self.client.get('/auth/demo-login/company')
        res = self.client.get('/company/profile')
        self.assertEqual(res.status_code, 200)
        res_jobs = self.client.get('/company/job_postings')
        self.assertEqual(res_jobs.status_code, 200)
        self.client.get('/auth/logout')

    def test_07_student_dashboard_render(self):
        """Verify Student dashboard renders cleanly."""
        self.client.get('/auth/demo-login/student')
        res = self.client.get('/student/profile')
        self.assertEqual(res.status_code, 200)
        res_jobs = self.client.get('/student/job_postings')
        self.assertEqual(res_jobs.status_code, 200)
        res_history = self.client.get('/student/history')
        self.assertEqual(res_history.status_code, 200)
        self.client.get('/auth/logout')

    def test_08_offer_authorization(self):
        """Verify student cannot accept another student's offer."""
        # Find an application
        app_item = Application.query.first()
        if app_item:
            # Create another student
            role_stud = Role.query.filter_by(name='student').first()
            intruder = User(name="Intruder", email="intruder@test.com", password="pw", contact="4444444444", roles=role_stud)
            db.session.add(intruder)
            db.session.commit()
            intruder_details = Student(user_id=intruder.id, cgpa=7.5, experience=0, skill_set="C++", resume="dummy.pdf")
            db.session.add(intruder_details)
            db.session.commit()

            # Login as intruder
            with self.client.session_transaction() as sess:
                sess['_user_id'] = str(intruder.id)

            res = self.client.get(f'/student/offer/join/{app_item.id}', follow_redirects=True)
            self.assertIn(b"Unauthorized access", res.data)

            # Clean up
            db.session.delete(intruder_details)
            db.session.delete(intruder)
            db.session.commit()

    def test_09_api_endpoints_and_authorization(self):
        """Test REST API endpoints with authentication and authorization."""
        # 1. Access API as Company
        self.client.get('/auth/demo-login/company')
        res_studs = self.client.get('/api/students')
        self.assertEqual(res_studs.status_code, 200)
        self.assertTrue(isinstance(res_studs.get_json(), list))

        res_comps = self.client.get('/api/companies')
        self.assertEqual(res_comps.status_code, 200)
        self.assertTrue(isinstance(res_comps.get_json(), list))
        self.client.get('/auth/logout')

        # 2. Update Student Profile via API
        self.client.get('/auth/demo-login/student')
        res_update = self.client.put('/api/student/update', json={"cgpa": 9.2, "skills": "Python, Flask, Docker, AWS"})
        self.assertEqual(res_update.status_code, 200)
        self.assertEqual(res_update.get_json()['student']['cgpa'], 9.2)
        self.client.get('/auth/logout')

    def test_10_company_job_ownership_protection(self):
        """Verify another company cannot close or mutate a different company's job."""
        job = JobPosition.query.first()
        if job:
            # Create a rival company
            role_comp = Role.query.filter_by(name='company').first()
            rival_user = User(name="Rival Corp", email="rival@test.com", password="pw", contact="9999999999", roles=role_comp)
            db.session.add(rival_user)
            db.session.commit()
            rival_comp = Company(user_id=rival_user.id, hr_name="Rival HR", employee_count=10, location="NY", website="http://rival.com", status="Approved")
            db.session.add(rival_comp)
            db.session.commit()

            # Login as rival company
            with self.client.session_transaction() as sess:
                sess['_user_id'] = str(rival_user.id)

            res = self.client.get(f'/company/job/close/{job.id}', follow_redirects=True)
            self.assertIn(b"Unauthorized access", res.data)

            # Clean up
            db.session.delete(rival_comp)
            db.session.delete(rival_user)
            db.session.commit()

if __name__ == '__main__':
    unittest.main()
