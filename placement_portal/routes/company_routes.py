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
        if current_user.company_details.is_approved == False:
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
            if current_user.company_details:
                return render_template('company/profile.html' , user=current_user)
            return render_template('company/setup.html' , user=current_user)
        else :
            flash('Unauthorized access', 'danger')
            return redirect(url_for('auth_bp.login'))

    if request.method == 'POST':
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
        if current_user.company_details and current_user.company_details.is_approved:
            flash('Your account is already approved!', 'success')
            return render_template('company/profile.html' , user=current_user)
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
        pending_jobs = [job for job in all_jobs if not job.is_approved]
        active_jobs = [job for job in all_jobs if job.is_approved]

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
    
    
@company_bp.route('/applications')
def applications():
    user_id = session['user_id']
    current_user = User.query.filter_by(id=user_id).first()
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))
    elif session.get('role') == 'company':
        if not current_user.company_details:
            flash('Please complete your profile first.', 'info')
            return redirect(url_for('company_bp.setup'))
        return render_template('company/applications.html' , user=current_user)
    else:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('auth_bp.login'))
    
    
    
@company_bp.route('/shortlisted')
def shortlisted():
    user_id = session['user_id']
    current_user = User.query.filter_by(id=user_id).first()
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))
    elif session.get('role') == 'company':
        if not current_user.company_details:
            flash('Please complete your profile first.', 'info')
            return redirect(url_for('company_bp.setup'))
        return render_template('company/shortlisted.html' , user=current_user)
    else:
        flash('Unauthorized access', 'danger')
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
    