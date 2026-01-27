from flask import Blueprint , current_app , render_template , session , flash , redirect , url_for , request
from controller.models import *
import os

student_bp = Blueprint('student_bp', __name__) 

@student_bp.route('/profile')
def profile():
    user_id = session['user_id']
    current_user = User.query.filter_by(id=user_id).first()
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))
    elif session.get('role') == 'student':
        if not current_user.student_details:
            flash('Please complete your profile first.', 'info')
            return redirect(url_for('student_bp.setup'))
        return render_template('student/profile.html' , user=current_user)
    else:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('auth_bp.login'))
    
    
@student_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    user_id = session['user_id']
    current_user = User.query.filter_by(id=user_id).first()
    if request.method == 'GET':
        if not session.get('user_id', None):
            return redirect(url_for('auth_bp.login'))    
        elif session.get('role') == 'student':
            if current_user.student_details:
                return render_template('student/profile.html' , user=current_user)
            return render_template('student/setup.html' , user=current_user)
        else :
            flash('Unauthorized access', 'danger')
            return redirect(url_for('auth_bp.login'))

    if request.method == 'POST':
        cgpa = float(request.form.get('cgpa'))
        experience = request.form.get('experience')
        skills = request.form.get('skill_set')
        milestones = request.form.get('milestones')
        
        # --- RESUME SAVING LOGIC ---
        resume = None 
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename != '':
                filename = os.path.basename(file.filename) # Prevents directory traversal
                save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'Resumes' , filename)
                file.save(save_path)

                resume = f"/static/uploads/Resumes/{filename}"
            
        # --- CREATE STUDENT RECORD ---
        skills = ', '.join(word.capitalize().strip() for word in skills.split(','))
        user_id = session['user_id']
        new_student = Student(
            user_id=user_id, # Link to the currently logged in User
            cgpa=cgpa,
            experience=experience,
            skill_set=skills,
            resume=resume,
            milestones=milestones
        )
        
        db.session.add(new_student)
        db.session.commit()
        
        flash('Profile Completed! Welcome to your profile.', 'success')
        return redirect(url_for('student_bp.profile'))

    return render_template('student/setup.html')


@student_bp.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    user_id = session['user_id']
    current_user = User.query.filter_by(id=user_id).first()
    if request.method == 'GET':
        if not session.get('user_id', None):
            return redirect(url_for('auth_bp.login'))    
        elif session.get('role') == 'student':
            return render_template('student/edit.html' , user=current_user)
        else :
            flash('Unauthorized access', 'danger')
            return redirect(url_for('auth_bp.login'))

    if request.method == 'POST':
        try:
            name = request.form.get('name')
            
            current_user.name = name.strip().title()
            current_user.contact = request.form.get('contact')

            if 'profile_pic' in request.files:
                file = request.files['profile_pic']
                if file and file.filename != '':
                    filename = os.path.basename(file.filename) # Prevents directory traversal
                    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'Profile_pics' , filename)
                    file.save(save_path)

                    current_user.image_url = f"/static/uploads/Profile_pics/{filename}"

            # --- Update Student Table (Specific Fields) ---
            student = current_user.student_details
            skills = request.form.get('skill_set')
            skills = ' , '.join(word.capitalize().strip() for word in skills.split(','))
            
            student.cgpa = float(request.form.get('cgpa'))
            student.experience = int(request.form.get('experience'))
            student.skill_set = skills
            student.milestones = request.form.get('milestones')
            
            if 'resume' in request.files:
                file = request.files['resume']
                if file and file.filename != '':
                    filename = os.path.basename(file.filename)
                    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'Resumes' , filename)
                    file.save(save_path)

                    student.resume = f"/static/uploads/Resumes/{filename}"

            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('student_bp.profile'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')
            return render_template('student/edit.html')
        
    return render_template('student/edit.html', user=current_user)



# --- MANAGE JOB_POSTINGS ROUTE ---
@student_bp.route('/job_postings')
def job_postings():
    # 1. AUTHENTICATION
    user_id = session['user_id']
    current_user = User.query.filter_by(id=user_id).first()
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))  
    elif session.get('role') == 'student':
        
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
                    (JobPosition.requirements.ilike(search))     
            )
        
        all_jobs = query.filter(JobPosition.is_approved).order_by(JobPosition.created_at.desc()).all()

        return render_template('student/job_postings.html', 
                               user=current_user,
                               search=search_query,
                               jobs = all_jobs,
                               active_page='job_postings')
    else:
        return redirect(url_for('auth_bp.login'))
    
    
@student_bp.route('/job/view/<int:id>')
def view_job(id):
    user_id = session['user_id']
    current_user = User.query.filter_by(id=user_id).first()
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))  
    elif session.get('role') == 'student':
        job = JobPosition.query.get_or_404(id)
        return render_template('student/view_job.html', 
                               job=job, 
                               user=current_user,
                               active_page='job_postings')
    else:
        return redirect(url_for('auth_bp.login'))




@student_bp.route('/job/apply/<int:id>', methods=['GET', 'POST'])
def apply_job(id):
    user_id = session['user_id']
    current_user = User.query.get(user_id)
    student = current_user.student_details
    # 1. AUTH CHECK
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))
    
    elif session.get('role') == 'student':
        
        # 2. GET JOB DETAILS
        job = JobPosition.query.get_or_404(id)
        
        # 3. CHECK DUPLICATE APPLICATION
        # We check if this student has already applied to this specific job_position_id
        existing_app = Application.query.filter_by(
            student_id=student.id, 
            job_position_id=job.id
        ).first()

        if existing_app:
            flash(f'You have already applied for the {job.job_title} position.', 'warning')
            return redirect(url_for('student_bp.job_postings'))

        # 4. HANDLE POST REQUEST (Form Submission)
        if request.method == 'POST':
            try:
                cover_letter_text = request.form.get('cover_letter')

                 # --- RESUME SAVING LOGIC ---
                resume = None 
                if 'resume' in request.files:
                    file = request.files['resume']
                    if file and file.filename != '':
                        filename = os.path.basename(file.filename) # Prevents directory traversal
                        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'Resumes' , filename)
                        file.save(save_path)

                        resume = f"/static/uploads/Resumes/{filename}"

                # C. Create Application Entry
                new_application = Application(
                    student_id=student.id,
                    job_position_id=job.id,
                    application_status='Applied',
                    cover_letter=cover_letter_text,
                    custom_resume=resume 
                )
                
                db.session.add(new_application)
                db.session.commit()
                
                flash('Application submitted successfully! Good luck.', 'success')
                return redirect(url_for('student_bp.job_postings')) 
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error submitting application: {str(e)}', 'danger')
                return redirect(url_for('student_bp.apply_job', id=id))

        # 5. HANDLE GET REQUEST (Show Form)
        return render_template('student/apply_job.html', 
                               user=current_user, 
                               job=job,
                               active_page='dashboard')
    
    else:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('auth_bp.login'))
    
    
    
@student_bp.route('/applications')
def applications():
    user_id = session['user_id']
    current_user = User.query.filter_by(id=user_id).first()
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))
    elif session.get('role') == 'student':
        if not current_user.student_details:
            flash('Please complete your profile first.', 'info')
            return redirect(url_for('student_bp.setup'))
        return render_template('student/applications.html' , user=current_user)
    else:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('auth_bp.login'))
    
    
    
@student_bp.route('/notifications')
def notifications():
    user_id = session['user_id']
    current_user = User.query.filter_by(id=user_id).first()
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))
    elif session.get('role') == 'student':
        if not current_user.student_details:
            flash('Please complete your profile first.', 'info')
            return redirect(url_for('student_bp.setup'))
        return render_template('student/notifications.html' , user=current_user)
    else:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('auth_bp.login'))
    
    
    
@student_bp.route('/history')
def history():
    user_id = session['user_id']
    current_user = User.query.filter_by(id=user_id).first()
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))
    elif session.get('role') == 'student':
        if not current_user.student_details:
            flash('Please complete your profile first.', 'info')
            return redirect(url_for('student_bp.setup'))
        return render_template('student/history.html' , user=current_user)
    else:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('auth_bp.login'))