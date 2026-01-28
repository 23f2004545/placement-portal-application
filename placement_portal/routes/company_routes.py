from flask import Blueprint , current_app , render_template , session , flash , redirect , url_for , request
from controller.models import *
import os

company_bp = Blueprint('company_bp', __name__) 

@company_bp.route('/profile')
def profile():
    user_id = session['user_id']
    current_user = User.query.filter_by(id=user_id).first()
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))   
    elif session.get('role') == 'company':
        if not current_user.company_details:
            flash('Please complete your profile first.', 'info')
            return redirect(url_for('company_bp.setup'))
        if current_user.company_details.status != "Approved":
            return redirect(url_for('company_bp.verification'))
        return render_template('company/profile.html' , user=current_user)
    else:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('auth_bp.login'))
    
    
    
@company_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    user_id = session['user_id']
    current_user = User.query.filter_by(id=user_id).first()
    if request.method == 'GET':
        if not session.get('user_id', None):
            return redirect(url_for('auth_bp.login'))    
        elif session.get('role') == 'company':
            if current_user.company_details.status != "Approved":
                return render_template('company/setup.html' , user=current_user)
            if current_user.company_details:
                return render_template('company/profile.html' , user=current_user)
            return render_template('company/setup.html' , user=current_user)
        else :
            flash('Unauthorized access', 'danger')
            return redirect(url_for('auth_bp.login'))

    if request.method == 'POST':
        if current_user.company_details and current_user.company_details.status == "Rejected":
            current_user.company_details.user_id=user_id, # Link to the currently logged in User
            current_user.company_details.hr_name=hr_name,
            current_user.company_details.employee_count=employee_count,
            current_user.company_details.location=location,
            current_user.company_details.website=website,
            current_user.company_details.description=description
            current_user.company_details.status = "Pending"
            db.session.commit()
            return redirect(url_for('company_bp.verification'))
        else:    
            hr_name = request.form.get('hr_name')
            employee_count = request.form.get('employee_count')
            location = request.form.get('location')
            website = request.form.get('website') 
            description = request.form.get('description')
            
            hr_name = hr_name.strip().title()        
            location = location.strip().title()        
            # --- CREATE company RECORD ---
            user_id = session['user_id']
            new_company = Company(
                user_id=user_id, # Link to the currently logged in User
                hr_name=hr_name,
                employee_count=employee_count,
                location=location,
                website=website,
                description=description
            )
            
            db.session.add(new_company)
            db.session.commit()
        
        flash('Profile Completed.', 'success')
        return redirect(url_for('company_bp.verification'))

    return render_template('company/setup.html')

# --- 3. THE WAITING ROOM ROUTE ---
@company_bp.route('/verification')
def verification():
    user_id = session['user_id']
    current_user = User.query.filter_by(id=user_id).first()
    if not session.get('user_id', None):
            return redirect(url_for('auth_bp.login'))    
    elif session.get('role') == 'company':
        if current_user.company_details and current_user.company_details.status == "Approved":
            flash('Your account is already approved!', 'success')
            return render_template('company/profile.html' , user=current_user)
        if current_user.company_details.status == "Rejected" :
            flash('Your company profile was rejected. Please retry.', 'danger')
            return render_template('company/retry.html' , user=current_user)
        flash('Your company profile is under review. Please wait for approval.', 'info')
        return render_template('company/wait.html' , user=current_user)    
    else :
        flash('Unauthorized access', 'danger')
        return redirect(url_for('auth_bp.login'))
    
    
@company_bp.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    user_id = session['user_id']
    current_user = User.query.filter_by(id=user_id).first()
    if request.method == 'GET':
        if not session.get('user_id', None):
            return redirect(url_for('auth_bp.login'))    
        elif session.get('role') == 'company':
            return render_template('company/edit.html' , user=current_user)
        else :
            flash('Unauthorized access', 'danger')
            return redirect(url_for('auth_bp.login'))
    
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            
            current_user.name = name.strip().title()
            current_user.contact = request.form.get('contact')

            if 'profile_pic' in request.files:
                pic = request.files['profile_pic']
                if pic and pic.filename != '':
                    filename = os.path.basename(pic.filename)
                    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'Profile_pics' , filename)
                    pic.save(save_path)
                    
                    current_user.image_url = f"/static/uploads/Profile_pics/{filename}"

            # --- Update Company Table (Business Info) ---
            company = current_user.company_details
            hr_name = request.form.get('hr_name')
            location = request.form.get('location')
            
            company.hr_name = hr_name.split().title()
            company.location = location.strip().title()
            company.website = request.form.get('website')
            company.description = request.form.get('description')

            db.session.commit()
            flash('Company profile updated successfully!', 'success')
            return redirect(url_for('company_bp.profile'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')
            return render_template('company/edit.html')

    # 2. GET: Show Form
    return render_template('company/edit.html', user=current_user)



# --- 3. THE JOB_POSTINGS ROUTE ---
@company_bp.route('/job_postings')
def job_postings():
    user_id = session['user_id']
    current_user = User.query.filter_by(id=user_id).first()
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))
    elif session.get('role') == 'company':
        if not current_user.company_details:
            flash('Please complete your profile first.', 'info')
            return redirect(url_for('company_bp.setup'))
        
        # 2. QUERY & JOINS
        # Join Job -> Company with current user's id
        company_id = current_user.company_details.id
        query = JobPosition.query.filter_by(company_id=company_id)
        
        # 3. SEARCH LOGIC
        search_query = request.args.get('q', '')
        if search_query:
            search = f"%{search_query}%"
            query = query.filter(
                    (JobPosition.job_title.ilike(search)) |   # Job Title
                    (JobPosition.job_status.ilike(search))   # Status (Hiring/Closed)
            )
        
        all_jobs = query.order_by(JobPosition.created_at.desc()).all()
        
        # 4. SEPARATE LISTS
        pending_jobs = [job for job in all_jobs if job.status == "Pending"]
        active_jobs = [job for job in all_jobs if job.status == "Approved"]

        return render_template('company/job_postings.html', 
                               user=current_user,
                               pending_jobs=pending_jobs,
                               active_jobs=active_jobs,
                               search=search_query,
                               jobs = all_jobs,
                               active_page='job_postings')
    else:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('auth_bp.login'))
    
@company_bp.route('/job/view/<int:id>')
def view_job(id):
    user_id = session['user_id']
    current_user = User.query.filter_by(id=user_id).first()
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))  
    elif session.get('role') == 'company':
        job = JobPosition.query.get_or_404(id)
        return render_template('company/view_job.html', 
                               job=job,
                               user=current_user,
                               active_page='job_postings')
    else:
        return redirect(url_for('auth_bp.login'))
    
@company_bp.route('/job/close/<int:id>')
def close_job(id):
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))  
    elif session.get('role') == 'company':
        
        job = JobPosition.query.get_or_404(id)
        job.job_status = "Closed"
        db.session.commit()
        
        flash(f'Job "{job.job_title}" has been closed.', 'warning')     
        return redirect(url_for('company_bp.job_postings'))
    else:
        return redirect(url_for('auth_bp.login'))
    
    
    
# --- 4. THE APPLICATIONS ROUTE ---
@company_bp.route('/applications')
def applications():
    # 1. AUTH CHECK
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))
    
    elif session.get('role') == 'company':
        user_id = session['user_id']
        current_user = User.query.get(user_id)
        
        if not current_user.company_details:
            flash('Please complete your profile first.', 'info')
            return redirect(url_for('company_bp.setup'))

        # 2. QUERY: Get applications ONLY for this company's jobs
        # Logic: Join Application -> JobPosition -> Filter by Company ID
        my_company_id = current_user.company_details.id
        
        query = Application.query.join(JobPosition).filter(
            JobPosition.company_id == my_company_id
        )

        # 3. SEARCH & FILTER
        search_query = request.args.get('q', '')

        if search_query:
            search = f"%{search_query}%"
            # We need to join Student & User to search by applicant Name
            query = query.join(Student).join(User).filter(
                (User.name.ilike(search)) |               # Applicant Name
                (JobPosition.job_title.ilike(search))     # Job Title
            )

        # Execute Query (Newest First)
        my_applications = query.filter(Application.application_status=="Applied").order_by(Application.applied_at.desc()).all()

        return render_template('company/applications.html', 
                               user=current_user,
                               applications=my_applications,
                               search=search_query,
                               active_page='applications')
    else:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('auth_bp.login'))    
    

@company_bp.route('/application/shortlist/<int:id>')
def shortlist_application(id):
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))  
    elif session.get('role') == 'company':
        
        application = Application.query.get_or_404(id)
        application.application_status = "Shortlisted"
        db.session.commit()
        
        flash(f'Application has been shortlisted.', 'info')     
        return redirect(url_for('company_bp.applications'))
    else:
        return redirect(url_for('auth_bp.login'))
    
    
@company_bp.route('/application/reject/<int:id>')
def reject_application(id):
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))  
    elif session.get('role') == 'company':
        
        application = Application.query.get_or_404(id)
        application.application_status = "Rejected"
        db.session.commit()
        
        flash(f'Application has been rejected.', 'danger')     
        return redirect(url_for('company_bp.reviewed'))
    else:
        return redirect(url_for('auth_bp.login'))

        

# --- 4. THE REVIEWED APPLICATIONS ROUTE ---
@company_bp.route('/reviewed')
def reviewed():
    # 1. AUTH CHECK
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))
    
    elif session.get('role') == 'company':
        user_id = session['user_id']
        current_user = User.query.get(user_id)
        
        if not current_user.company_details:
            flash('Please complete your profile first.', 'info')
            return redirect(url_for('company_bp.setup'))

        # 2. QUERY: Get applications ONLY for this company's jobs
        # Logic: Join Application -> JobPosition -> Filter by Company ID
        my_company_id = current_user.company_details.id
        
        query = Application.query.join(JobPosition).filter(
            JobPosition.company_id == my_company_id
        )

        # 3. SEARCH & FILTER
        search_query = request.args.get('q', '')
        status_filter = request.args.get('status', '')

        if search_query:
            search = f"%{search_query}%"
            # We need to join Student & User to search by applicant Name
            query = query.join(Student).join(User).filter(
                (User.name.ilike(search)) |               # Applicant Name
                (JobPosition.job_title.ilike(search))     # Job Title
            )
        
        if status_filter:
            query = query.filter(Application.application_status == status_filter)

        # Execute Query (Newest First)
        my_applications = query.filter(Application.application_status!="Applied").order_by(Application.applied_at.desc()).all()

        return render_template('company/reviewed.html', 
                               user=current_user,
                               applications=my_applications,
                               search=search_query,
                               status=status_filter,
                               active_page='reviewed')
    else:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('auth_bp.login'))



@company_bp.route('/application/select/<int:id>')
def select_application(id):
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))  
    elif session.get('role') == 'company':
        
        application = Application.query.get_or_404(id)
        application.application_status = "Selected"
        db.session.commit()
        
        flash(f'Application has been selected.', 'success')     
        return redirect(url_for('company_bp.reviewed'))
    else:
        return redirect(url_for('auth_bp.login'))
    
    


@company_bp.route('/application/view/<int:id>')
def view_application(id):
    user_id = session['user_id']
    current_user = User.query.filter_by(id=user_id).first()
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))  
    elif session.get('role') == 'company':
        application = Application.query.get_or_404(id)
        return render_template('company/view_application.html', 
                               application=application,
                               user=current_user,
                               active_page='job_postings')
    else:
        return redirect(url_for('auth_bp.login'))




@company_bp.route('/jobs/create', methods=['GET', 'POST'])
def create_job():
    user_id = session['user_id']
    current_user = User.query.filter_by(id=user_id).first()
    if request.method == 'GET':
        if not session.get('user_id', None):
            return redirect(url_for('auth_bp.login'))    
        elif session.get('role') == 'company':
            return render_template('company/create_job.html' , user=current_user)
        else :
            flash('Unauthorized access', 'danger')
            return redirect(url_for('auth_bp.login'))
        
        
    if request.method == 'POST':
        try:
            new_job = JobPosition(
                company_id=current_user.company_details.id,
                job_title=request.form.get('job_title'),
                job_type=request.form.get('job_type'),
                job_pay=request.form.get('job_pay'),
                job_timing=request.form.get('job_timing'),
                job_location=request.form.get('job_location'),
                requirements=request.form.get('requirements'),
                job_description=request.form.get('job_description'),
                job_status='Hiring'
            )

            db.session.add(new_job)
            db.session.commit()
            
            flash('Job posted successfully! Waiting for company approval.', 'success')
            return redirect(url_for('company_bp.job_postings'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error posting job: {str(e)}', 'danger')
            return redirect(url_for('company_bp.create_job'))

    return render_template('company/create_job.html', user=current_user)
    