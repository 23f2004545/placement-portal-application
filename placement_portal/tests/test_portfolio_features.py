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

            # Clean up (deleting intruder cascades to intruder_details)
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

            # Clean up (deleting rival_user cascades to rival_comp)
            db.session.delete(rival_user)
            db.session.commit()

    def test_11_dynamic_onclick_seeding_and_rich_dataset(self):
        """Verify dynamic on-click demo seeding generates rich baseline dataset without impacting real users."""
        # 1. Access dynamic route /login/demo/student
        res = self.client.get('/login/demo/student', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Logged in as Demo Student", res.data)
        self.client.get('/auth/logout')

        # 2. Verify baseline dataset counts
        demo_companies = Company.query.join(User).filter(User.email.like('%@portfolio.demo')).all()
        self.assertGreaterEqual(len(demo_companies), 2)

        demo_students = Student.query.join(User).filter(User.email.like('%@portfolio.demo')).all()
        self.assertGreaterEqual(len(demo_students), 2)

        demo_jobs = JobPosition.query.join(Company).join(User).filter(User.email.like('%@portfolio.demo')).all()
        self.assertGreaterEqual(len(demo_jobs), 2)

        demo_apps = Application.query.join(Student).join(User).filter(User.email.like('%@portfolio.demo')).all()
        self.assertGreaterEqual(len(demo_apps), 2)

    def test_12_cascade_deletions(self):
        """Verify cascading deletion cleanly removes child entities (User -> Student/Company -> Job -> App -> Placement)."""
        role_stud = Role.query.filter_by(name='student').first()
        role_comp = Role.query.filter_by(name='company').first()

        # Create temporary company, job, student, application, and placement
        c_user = User(name="Cascade Co", email="cascade_co@test.com", password="pw", contact="1112223334", roles=role_comp)
        db.session.add(c_user)
        db.session.commit()
        co = Company(user_id=c_user.id, hr_name="Cascade HR", employee_count=50, location="Remote", website="http://c.com")
        db.session.add(co)
        db.session.commit()

        job = JobPosition(company_id=co.id, job_title="Cascade Eng", requirements="None", job_location="Remote", job_pay="100k", job_type="Remote", job_timing="Full Time")
        db.session.add(job)
        db.session.commit()

        s_user = User(name="Cascade Student", email="cascade_st@test.com", password="pw", contact="5556667778", roles=role_stud)
        db.session.add(s_user)
        db.session.commit()
        st = Student(user_id=s_user.id, cgpa=9.0, experience=0, skill_set="Testing", resume="test.pdf")
        db.session.add(st)
        db.session.commit()

        app_obj = Application(student_id=st.id, job_position_id=job.id, application_status="Selected")
        db.session.add(app_obj)
        db.session.commit()

        plc = Placement(application_id=app_obj.id, salary_offered="100k", joining_date="Tomorrow", offer_letter="offer.pdf")
        db.session.add(plc)
        db.session.commit()

        app_id = app_obj.id
        plc_id = plc.id
        job_id = job.id
        co_id = co.id
        st_id = st.id

        # Delete student user -> should cascade to Student, Application, Placement
        db.session.delete(s_user)
        db.session.commit()

        self.assertIsNone(Student.query.get(st_id))
        self.assertIsNone(Application.query.get(app_id))
        self.assertIsNone(Placement.query.get(plc_id))

        # Delete company user -> should cascade to Company and JobPosition
        db.session.delete(c_user)
        db.session.commit()

        self.assertIsNone(Company.query.get(co_id))
        self.assertIsNone(JobPosition.query.get(job_id))

    def test_13_demo_admin_guardrails_protect_real_users(self):
        """Verify demo admin cannot delete, blacklist, or reject real users (faux-success protection)."""
        # 1. Create a real student and real company
        role_stud = Role.query.filter_by(name='student').first()
        role_comp = Role.query.filter_by(name='company').first()

        real_stud_user = User(name="Real Student", email="real_student@university.edu", password="pw", contact="7778889990", roles=role_stud)
        db.session.add(real_stud_user)
        db.session.commit()
        real_stud = Student(user_id=real_stud_user.id, cgpa=8.5, experience=1, skill_set="Java", resume="res.pdf")
        db.session.add(real_stud)

        real_comp_user = User(name="Real Enterprise", email="real_recruiter@enterprise.org", password="pw", contact="8889990001", roles=role_comp)
        db.session.add(real_comp_user)
        db.session.commit()
        real_comp = Company(user_id=real_comp_user.id, hr_name="Real HR", employee_count=200, location="Chicago", website="http://real.org")
        db.session.add(real_comp)
        db.session.commit()

        real_job = JobPosition(company_id=real_comp.id, job_title="Real Architect", requirements="AWS", job_location="Chicago", job_pay="150k", job_type="Onsite", job_timing="Full Time")
        db.session.add(real_job)
        db.session.commit()

        # 2. Login as Demo Admin
        self.client.get('/auth/demo-login/admin')

        # 3. Attempt to Blacklist Real Student -> should simulate success but NOT modify database
        res_bl_stud = self.client.get(f'/admin/student/blacklist/{real_stud.id}', follow_redirects=True)
        self.assertEqual(res_bl_stud.status_code, 200)
        self.assertIn(b"has been Blacklisted", res_bl_stud.data)
        db.session.refresh(real_stud_user)
        self.assertFalse(real_stud_user.blacklisted)  # Intercepted! Remained False

        # 4. Attempt to Delete Real Student -> should simulate success but NOT modify database
        res_del_stud = self.client.get(f'/admin/student/delete/{real_stud.id}', follow_redirects=True)
        self.assertEqual(res_del_stud.status_code, 200)
        self.assertIn(b"Student profile deleted", res_del_stud.data)
        db.session.refresh(real_stud)
        self.assertFalse(real_stud.is_deleted)  # Intercepted! Remained False

        # 5. Attempt to Blacklist Real Company -> should simulate success but NOT modify database
        res_bl_comp = self.client.get(f'/admin/company/blacklist/{real_comp.id}', follow_redirects=True)
        self.assertEqual(res_bl_comp.status_code, 200)
        self.assertIn(b"has been Blacklisted", res_bl_comp.data)
        db.session.refresh(real_comp_user)
        self.assertFalse(real_comp_user.blacklisted)  # Intercepted! Remained False

        # 6. Attempt to Delete Real Company -> should simulate success but NOT modify database
        res_del_comp = self.client.get(f'/admin/company/delete/{real_comp.id}', follow_redirects=True)
        self.assertEqual(res_del_comp.status_code, 200)
        self.assertIn(b"Company profile deleted", res_del_comp.data)
        db.session.refresh(real_comp)
        self.assertFalse(real_comp.is_deleted)  # Intercepted! Remained False

        # 7. Attempt to Reject/Delete Real Job -> should simulate success but NOT delete job
        res_rej_job = self.client.get(f'/admin/job/reject/{real_job.id}', follow_redirects=True)
        self.assertEqual(res_rej_job.status_code, 200)
        self.assertIn(b"has been rejected", res_rej_job.data)
        self.assertIsNotNone(JobPosition.query.get(real_job.id))  # Intercepted! Job still exists

        # Clean up real test accounts
        self.client.get('/auth/logout')
        db.session.delete(real_stud_user)
        db.session.delete(real_comp_user)
        db.session.commit()

    def test_14_demo_admin_allows_natural_action_on_demo_users(self):
        """Verify demo admin actions on demo users execute naturally."""
        # 1. Login as Demo Admin
        self.client.get('/auth/demo-login/admin')

        # 2. Find demo student
        demo_stud = Student.query.join(User).filter(User.email == 'student@portfolio.demo').first()
        self.assertIsNotNone(demo_stud)

        # 3. Toggle blacklist on demo student -> should actually toggle
        initial_status = demo_stud.user.blacklisted
        res = self.client.get(f'/admin/student/blacklist/{demo_stud.id}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        db.session.refresh(demo_stud.user)
        self.assertNotEqual(demo_stud.user.blacklisted, initial_status)

        # Reset blacklist for subsequent tests
        demo_stud.user.blacklisted = False
        db.session.commit()
        self.client.get('/auth/logout')

    def test_15_demo_names_and_admin_ui_guardrails(self):
        """Verify seeded entity names have (Demo) and Admin banner & micro-text render for demo admin."""
        # 1. Verify seeded entity names
        c1 = User.query.filter_by(email='company@portfolio.demo').first()
        c2 = User.query.filter_by(email='cloudscale@portfolio.demo').first()
        s1 = User.query.filter_by(email='student@portfolio.demo').first()
        s2 = User.query.filter_by(email='student2@portfolio.demo').first()

        self.assertIsNotNone(c1)
        self.assertEqual(c1.name, "Nexus Tech Innovations (Demo)")
        self.assertIsNotNone(c2)
        self.assertEqual(c2.name, "CloudScale AI Labs (Demo)")
        self.assertIsNotNone(s1)
        self.assertEqual(s1.name, "Alex Morgan (Demo)")
        self.assertIsNotNone(s2)
        self.assertEqual(s2.name, "Priya Sharma (Demo)")

        # 2. Login as Demo Admin and check Admin Banner
        self.client.get('/auth/demo-login/admin')
        res_profile = self.client.get('/admin/profile')
        self.assertEqual(res_profile.status_code, 200)
        self.assertIn(b"Demo Environment Active", res_profile.data)
        self.assertIn(b"To protect live user data, destructive actions", res_profile.data)

        # 3. Check Action Micro-text on companies page
        res_comps = self.client.get('/admin/companies')
        self.assertEqual(res_comps.status_code, 200)
        self.assertIn(b"*Note: Actions on real accounts are simulated. Use (Demo) tagged profiles to test live data cascading.*", res_comps.data)

        # 4. Check Action Micro-text on students page
        res_studs = self.client.get('/admin/students')
        self.assertEqual(res_studs.status_code, 200)
        self.assertIn(b"*Note: Actions on real accounts are simulated. Use (Demo) tagged profiles to test live data cascading.*", res_studs.data)

        # 5. Check Action Micro-text on job postings page
        res_jobs = self.client.get('/admin/job_postings')
        self.assertEqual(res_jobs.status_code, 200)
        self.assertIn(b"*Note: Actions on real accounts are simulated. Use (Demo) tagged profiles to test live data cascading.*", res_jobs.data)

        self.client.get('/auth/logout')

if __name__ == '__main__':
    unittest.main()

