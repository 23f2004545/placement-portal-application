from flask import Blueprint , current_app , render_template , session , flash , redirect , url_for , request
from controller.models import *

admin_bp = Blueprint('admin_bp', __name__) 

@admin_bp.route('/profile')
def profile():
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))  
    elif session.get('role') == 'admin':
        return render_template('admin/profile.html')
    else:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('auth_bp.login'))
    
    
    
# --- MANAGE COMPANIES ROUTE ---
@admin_bp.route('/companies')
def companies():
    # 1. AUTHENTICATION CHECK (As requested)
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))  
    elif session.get('role') == 'admin':
        
        # 2. LOGIC START
        search_query = request.args.get('q', '')
        
        # Join Company with User to access name, email, image, etc.
        query = Company.query.join(User)

        if search_query:
            search = f"%{search_query}%"
            # Search by Company Name (User.name) or HR Name
            query = query.filter(
                (User.name.ilike(search)) | 
                (Company.hr_name.ilike(search)) |
                (Company.id.ilike(search))
            )

        all_companies = query.all()

        # Separate into lists based on 'is_approved'
        pending_list = [c for c in all_companies if not c.is_approved]
        approved_list = [c for c in all_companies if c.is_approved]

        return render_template('admin/companies.html', 
                               user=User.query.get(session['user_id']), # Current Admin User
                               pending_companies=pending_list,
                               approved_companies=approved_list,
                               companies=all_companies,
                               search = search_query,
                               active_page='companies')
    else:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('auth_bp.login'))

# --- ACTION: APPROVE COMPANY ---
@admin_bp.route('/company/approve/<int:id>')
def approve_company(id):
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))  
    elif session.get('role') == 'admin':
        
        company = company.query.get_or_404(id)
        company.is_approved = True
        db.session.commit()
        
        flash(f'{company.user.name} has been approved.', 'success')
        return redirect(url_for('admin_bp.companies'))
    else:
        return redirect(url_for('auth_bp.login'))

# --- ACTION: BLACKLIST TOGGLE ---
@admin_bp.route('/company/blacklist/<int:id>')
def toggle_blacklist_company(id):
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))  
    elif session.get('role') == 'admin':
        
        company = company.query.get_or_404(id)
        # Toggle the User's blacklist status
        company.user.blacklisted = not company.user.blacklisted
        db.session.commit()
        
        status = "Blacklisted" if company.user.blacklisted else "Reactivated"
        flash(f'{company.user.name} has been {status}.', 'info')
        return redirect(url_for('admin_bp.companies'))
    else:
        return redirect(url_for('auth_bp.login'))

# --- ACTION: DELETE COMPANY ---
@admin_bp.route('/company/delete/<int:id>')
def delete_company(id):
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))  
    elif session.get('role') == 'admin':
        
        company = company.query.get_or_404(id)
        user = company.user # Get the associated User account
        
        try:
            db.session.delete(company)
            db.session.delete(user) # Cascading delete usually handles this, but explicit is safer
            db.session.commit()
            flash('Company profile deleted.', 'warning')
        except Exception as e:
            db.session.rollback()
            flash('Error deleting company.', 'danger')
            
        return redirect(url_for('admin_bp.companies'))
    else:
        return redirect(url_for('auth_bp.login'))
    
@admin_bp.route('/company/view/<int:id>')
def view_company_profile(id):
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))  
    elif session.get('role') == 'admin':
        
        # Fetch the student (or 404 if not found)
        company = Company.query.get_or_404(id)
        
        return render_template('admin/view_company.html', 
                               company=company, 
                               user=User.query.get(session['user_id']), # Current Admin
                               active_page='companies')
    else:
        return redirect(url_for('auth_bp.login'))
    
    
# --- MANAGE STUDENTS ROUTE ---
@admin_bp.route('/students')
def students():
    # 1. AUTHENTICATION CHECK (As requested)
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))  
    elif session.get('role') == 'admin':
        
        # 2. LOGIC START
        search_query = request.args.get('q', '')
        
        # Join Student with User to access name, email, image, etc.
        query = Student.query.join(User)

        if search_query:
            search = f"%{search_query}%"
            # Search by Student Name (User.name) or ID or contact
            query = query.filter(
                (User.name.ilike(search)) | 
                (User.email.ilike(search)) |
                (Student.id.ilike(search))
            )

        all_students = query.all()

        return render_template('admin/students.html', 
                               user=User.query.get(session['user_id']), # Current Admin User
                               students=all_students,
                               search = search_query,
                               active_page='students')
    else:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('auth_bp.login'))

# --- ACTION: BLACKLIST TOGGLE ---
@admin_bp.route('/student/blacklist/<int:id>')
def toggle_blacklist_student(id):
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))  
    elif session.get('role') == 'admin':
        
        student = Student.query.get_or_404(id)
        # Toggle the User's blacklist status
        student.user.blacklisted = not student.user.blacklisted
        db.session.commit()
        
        status = "Blacklisted" if student.user.blacklisted else "Reactivated"
        flash(f'{student.user.name} has been {status}.', 'info')
        return redirect(url_for('admin_bp.students'))
    else:
        return redirect(url_for('auth_bp.login'))

# --- ACTION: DELETE STUDENT ---
@admin_bp.route('/student/delete/<int:id>')
def delete_student(id):
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))  
    elif session.get('role') == 'admin':
        
        student = Student.query.get_or_404(id)
        user = student.user # Get the associated User account
        
        try:
            db.session.delete(student)
            db.session.delete(user) # Cascading delete usually handles this, but explicit is safer
            db.session.commit()
            flash('Student profile deleted.', 'warning')
        except Exception as e:
            db.session.rollback()
            flash('Error deleting student.', 'danger')
            
        return redirect(url_for('admin_bp.students'))
    else:
        return redirect(url_for('auth_bp.login'))
    
@admin_bp.route('/student/view/<int:id>')
def view_student_profile(id):
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))  
    elif session.get('role') == 'admin':
        
        # Fetch the student (or 404 if not found)
        student = Student.query.get_or_404(id)
        
        return render_template('admin/view_student.html', 
                               student=student, 
                               user=User.query.get(session['user_id']), # Current Admin
                               active_page='students')
    else:
        return redirect(url_for('auth_bp.login'))
    
    
    
# --- MANAGE JOB_POSTINGS ROUTE ---
@admin_bp.route('/job_postings')
def job_postings():
    # 1. AUTHENTICATION
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))  
    elif session.get('role') == 'admin':
        
        # 2. QUERY & JOINS
        # Join Job -> Company -> User (to get Company Name & Logo)
        query = JobPosition.query.join(Company).join(User)
        
        # 3. SEARCH LOGIC
        search_query = request.args.get('q', '')
        if search_query:
            search = f"%{search_query}%"
            query = query.filter(
                    (JobPosition.job_title.ilike(search)) |   # Job Title
                    (User.name.ilike(search)) |               # Company Name
                    (JobPosition.job_type.ilike(search)) |    # Type (Remote/Hybrid)
                    (JobPosition.job_status.ilike(search))   # Status (Hiring/Closed)
            )
        
        all_jobs = query.order_by(JobPosition.created_at.desc()).all()

        # 4. SEPARATE LISTS
        pending_jobs = [job for job in all_jobs if not job.is_approved]
        active_jobs = [job for job in all_jobs if job.is_approved]

        return render_template('admin/job_postings.html', 
                               user=User.query.get(session['user_id']),
                               pending_jobs=pending_jobs,
                               active_jobs=active_jobs,
                               search=search_query,
                               jobs = all_jobs,
                               active_page='job_postings')
    else:
        return redirect(url_for('auth_bp.login'))

# --- ACTION: APPROVE JOB ---
@admin_bp.route('/job/approve/<int:id>')
def approve_job(id):
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))  
    elif session.get('role') == 'admin':
        
        job = JobPosition.query.get_or_404(id)
        job.is_approved = True
        db.session.commit()
        
        flash(f'Job "{job.job_title}" has been approved.', 'success')
        return redirect(url_for('admin_bp.job_postings'))
    else:
        return redirect(url_for('auth_bp.login'))

# --- ACTION: VIEW JOB DETAILS (Route Placeholder) ---
@admin_bp.route('/job/view/<int:id>')
def view_job(id):
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))  
    elif session.get('role') == 'admin':
        job = JobPosition.query.get_or_404(id)
        return render_template('admin/view_job.html', 
                               job=job, 
                               user=User.query.get(session['user_id']),
                               active_page='job_postings')
    else:
        return redirect(url_for('auth_bp.login'))
    
# --- ACTION: DELETE JOB ---
@admin_bp.route('/job/delete/<int:id>')
def delete_job(id):
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))  
    elif session.get('role') == 'admin':
        
        job = job.query.get_or_404(id)
        
        try:
            db.session.delete(job)
            db.session.commit()
            flash('Job deleted.', 'warning')
        except Exception as e:
            db.session.rollback()
            flash('Error deleting Job.', 'danger')
            
        return redirect(url_for('admin_bp.job_postings'))
    else:
        return redirect(url_for('auth_bp.login'))
    
# @admin_bp.route('/job_postings')
# def job_postings():
#     if not session.get('user_id', None):
#         return redirect(url_for('auth_bp.login'))  
#     elif session.get('role') == 'admin':
#         return render_template('admin/job_postings.html')
#     else:
#         flash('Unauthorized access', 'danger')
#         return redirect(url_for('auth_bp.login'))
    
    
    
@admin_bp.route('/job_applications')
def job_applications():
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))  
    elif session.get('role') == 'admin':
        return render_template('admin/job_applications.html')
    else:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('auth_bp.login'))
    
    
