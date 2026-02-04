from flask import Blueprint , render_template  , flash , redirect , url_for , request
from controller.decorators import admin_required
from flask_login import current_user
from sqlalchemy import func
from datetime import datetime , timedelta
from controller.models import *

admin_bp = Blueprint('admin_bp', __name__) 


@admin_bp.route('/profile')
@admin_required
def profile():
    
# --- 1. KEY COUNTERS (Top Cards) ---
    stats = {
        'students': Student.query.count(),
        'companies': Company.query.count(),
        'jobs': JobPosition.query.count(),
        'placements': Placement.query.count()
    }

    # --- 2. CHART DATA: Application Status (Doughnut) ---
    # Query: [('Applied', 10), ('Selected', 2), ...]
    status_query = db.session.query(
        Application.application_status, func.count(Application.id)
    ).group_by(Application.application_status).all()
    
    app_status_labels = [s[0] for s in status_query]
    app_status_values = [s[1] for s in status_query]

    # --- 3. CHART DATA: Activity Trend (Line Chart - Last 7 Days) ---
    # We do this in Python to handle missing dates gracefully (so graph doesn't jump)
    today = datetime.now().date()
    dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    daily_counts = []
    
    for date_str in dates:
        # Count apps created on this specific date
        count = Application.query.filter(
            func.date(Application.applied_at) == date_str
        ).count()
        daily_counts.append(count)

    # --- 4. CHART DATA: Top Hiring Companies (Bar Chart) ---
    # Get top 5 companies by job count
    top_companies_query = db.session.query(
        User.name, func.count(JobPosition.id)
    ).join(Company, Company.user_id == User.id)\
     .join(JobPosition, JobPosition.company_id == Company.id)\
     .group_by(User.name)\
     .order_by(func.count(JobPosition.id).desc())\
     .limit(5).all()
     
    company_labels = [c[0] for c in top_companies_query]
    company_values = [c[1] for c in top_companies_query]
        
    return render_template('admin/profile.html',
                           stats=stats,
                           app_status_labels=app_status_labels,
                           app_status_values=app_status_values,
                           trend_dates=dates,
                           trend_values=daily_counts,
                           company_labels=company_labels,
                           company_values=company_values)

    
    
#  =========================================
#      ------ MANAGE COMPANIES --------
#  ========================================= 

@admin_bp.route('/companies')
@admin_required
def companies():
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

    # Separate into lists based on 'status'
    pending_list = [c for c in all_companies if c.status=="Pending"]
    approved_list = [c for c in all_companies if c.status=="Approved"]

    return render_template('admin/companies.html', 
                            user=current_user, 
                            pending_companies=pending_list,
                            approved_companies=approved_list,
                            companies=all_companies,
                            search = search_query)


# --- ACTION: APPROVE COMPANY ---
@admin_bp.route('/company/approve/<int:id>')
@admin_required
def approve_company(id):
    
    company = Company.query.get_or_404(id)
    company.status = "Approved"
    db.session.commit()
    
    flash(f'{company.user.name} has been approved.', 'success')
    return redirect(url_for('admin_bp.companies'))

    
# --- ACTION: REJECT COMPANY ---
@admin_bp.route('/company/reject/<int:id>', methods=['GET', 'POST'])
@admin_required
def reject_company(id):

    company = Company.query.get_or_404(id)
    if request.method == 'POST':
        try:
            
            rejection_reason = request.form.get('rejection_reason')
            company.rejection_reason = rejection_reason
            company.status = "Rejected"
            db.session.commit()
            
            flash(f'{company.user.name} has been rejected.', 'danger')
            return redirect(url_for('admin_bp.companies')) 
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error rejecting company: {str(e)}', 'danger')
            return redirect(url_for('admin_bp.companies', id=id))
    return render_template('admin/rejection.html', 
                            company=company)


# --- ACTION: BLACKLIST TOGGLE ---
@admin_bp.route('/company/blacklist/<int:id>')
@admin_required
def toggle_blacklist_company(id):
    
    company = Company.query.get_or_404(id)
    # Toggle the User's blacklist status
    company.user.blacklisted = not company.user.blacklisted
    db.session.commit()
    
    status = "Blacklisted" if company.user.blacklisted else "Reactivated"
    flash(f'{company.user.name} has been {status}.', 'info')
    return redirect(url_for('admin_bp.companies'))


# --- ACTION: DELETE COMPANY ---
@admin_bp.route('/company/delete/<int:id>')
@admin_required
def delete_company(id):
      
    company = Company.query.get_or_404(id)
    
    try:
        company.is_deleted = True 
        db.session.commit()
        flash('Company profile deleted.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting company.', 'danger')
        
    return redirect(url_for('admin_bp.companies'))

# --- ACTION: VIEW COMPANY ---
@admin_bp.route('/company/view/<int:id>')
@admin_required
def view_company_profile(id):

    # Fetch the Company (or 404 if not found)
    company = Company.query.get_or_404(id)
    
    return render_template('admin/view_company.html', 
                            company=company, 
                            user=current_user)
    

#  =========================================
#      ------ MANAGE STUDENTS --------
#  ========================================= 

@admin_bp.route('/students')
@admin_required
def students():

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
                            user=current_user, 
                            students=all_students,
                            search = search_query)


# --- ACTION: BLACKLIST TOGGLE ---
@admin_bp.route('/student/blacklist/<int:id>')
@admin_required
def toggle_blacklist_student(id):
   
    student = Student.query.get_or_404(id)
    # Toggle the User's blacklist status
    student.user.blacklisted = not student.user.blacklisted
    db.session.commit()
    
    status = "Blacklisted" if student.user.blacklisted else "Reactivated"
    flash(f'{student.user.name} has been {status}.', 'info')
    return redirect(url_for('admin_bp.students'))


# --- ACTION: DELETE STUDENT ---
@admin_bp.route('/student/delete/<int:id>')
@admin_required
def delete_student(id):
    
    student = Student.query.get_or_404(id)
    
    try:
        student.is_deleted = True
        db.session.commit()
        flash('Student profile deleted.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting student.', 'danger')
        
    return redirect(url_for('admin_bp.students'))


# --- ACTION: VIEW STUDENT ---
@admin_bp.route('/student/view/<int:id>')
@admin_required
def view_student_profile(id):
        
    # Fetch the student (or 404 if not found)
    student = Student.query.get_or_404(id)
    
    return render_template('admin/view_student.html', 
                            student=student, 
                            user=current_user)

    
    
#  =========================================
#     ------ MANAGE JOB POSTINGS -------
#  =========================================
 
@admin_bp.route('/job_postings')
@admin_required
def job_postings():
    
    # Join Job -> Company -> User (to get Company Name & Logo)
    query = JobPosition.query.join(Company).join(User)
    
    # SEARCH LOGIC
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

    # SEPARATE LISTS
    pending_jobs = [job for job in all_jobs if job.status=="Pending"]
    active_jobs = [job for job in all_jobs if job.status=="Approved"]

    return render_template('admin/job_postings.html', 
                            user=current_user,
                            pending_jobs=pending_jobs,
                            active_jobs=active_jobs,
                            search=search_query,
                            jobs = all_jobs)


# --- ACTION: APPROVE JOB ---
@admin_bp.route('/job/approve/<int:id>')
@admin_required
def approve_job(id):
  
    job = JobPosition.query.get_or_404(id)
    job.status = "Approved"
    db.session.commit()
    
    flash(f'Job "{job.job_title}" has been approved.', 'success')
    return redirect(url_for('admin_bp.job_postings'))

    
# --- ACTION: REJECT JOB ---
@admin_bp.route('/job/reject/<int:id>')
@admin_required
def reject_job(id):
    
    job = JobPosition.query.get_or_404(id)
    db.session.delete(job)
    db.session.commit()
    
    flash(f'Job "{job.job_title}" has been rejected.', 'danger')
    return redirect(url_for('admin_bp.job_postings'))


# --- ACTION: VIEW JOB DETAILS ---
@admin_bp.route('/job/view/<int:id>')
@admin_required
def view_job(id):

    job = JobPosition.query.get_or_404(id)
    return render_template('admin/view_job.html', 
                            job=job, 
                            user=current_user)

    
# --- ACTION: DELETE JOB ---
@admin_bp.route('/job/delete/<int:id>')
@admin_required
def delete_job(id):

    job = JobPosition.query.get_or_404(id)
    
    try:
        job.is_deleted = True
        db.session.commit()
        flash('Job deleted.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting Job.', 'danger')
        
    return redirect(url_for('admin_bp.job_postings'))

    
#  =========================================
#   ------ MANAGE JOB APPLICATIONS -------
#  =========================================

@admin_bp.route('/job_applications')
@admin_required
def job_applications():
    
    query = Application.query.join(JobPosition).join(Company).join(User)
    
    # SEARCH LOGIC
    search_query = request.args.get('q', '')
    status_filter = request.args.get('status', '')
    
    if search_query:
        search = f"%{search_query}%"
        query = query.filter(
                (JobPosition.job_title.ilike(search)) |   # Job Title
                (User.name.ilike(search))               # Company Name 
        )
    
    if status_filter:
        query = query.filter(Application.application_status == status_filter)
    
    all_applications = query.order_by(Application.applied_at.desc()).all()

    return render_template('admin/job_applications.html', 
                            user=current_user,
                            search=search_query,
                            status=status_filter,
                            applications = all_applications)       
    

# --- ACTION: VIEW APPLICATION ---
@admin_bp.route('/application/view/<int:id>')
@admin_required
def view_application(id):

    app = Application.query.get_or_404(id)
    
    return render_template('admin/view_application.html', 
                            application=app, 
                            user=current_user) 
