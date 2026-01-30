from flask import Blueprint , current_app , render_template , session , flash , redirect , url_for , request
from controller.decorators import student_required
from flask_login import current_user
from controller.models import *
import os

student_bp = Blueprint('student_bp', __name__) 

@student_bp.route('/profile')
@student_required
def profile():
    return render_template('student/profile.html' , user=current_user)

    
# --- ACTION: ACCOUNT SETUP ---
@student_bp.route('/setup', methods=['GET', 'POST'])
@student_required
def setup():

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
        user_id = current_user.id
        new_student = Student(
            user_id=user_id, 
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

    if current_user.student_details:
        return render_template('student/profile.html' , user=current_user)
    return render_template('student/setup.html' , user=current_user)


# --- ACTION: EDIT PROFILE ---
@student_bp.route('/profile/edit', methods=['GET', 'POST'])
@student_required
def edit_profile():

    if request.method == 'POST':
        try:
            name = request.form.get('name')
            
            current_user.name = name.strip().title()
            current_user.contact = request.form.get('contact')

            if 'profile_pic' in request.files:
                file = request.files['profile_pic']
                if file and file.filename != '':
                    filename = os.path.basename(file.filename) 
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
        
    return render_template('student/edit.html' , user=current_user)


# --- MANAGE JOB_POSTINGS ROUTE ---
@student_bp.route('/job_postings')
@student_required
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
                (JobPosition.requirements.ilike(search))     
        )
    
    all_jobs = query.filter(JobPosition.status=="Approved" , JobPosition.is_deleted==False).order_by(JobPosition.created_at.desc()).all()

    return render_template('student/job_postings.html', 
                            user=current_user,
                            search=search_query,
                            jobs = all_jobs,
                            active_page='job_postings')

    
# --- ACTION: VIEW JOB ---
@student_bp.route('/job/view/<int:id>')
@student_required
def view_job(id):

    job = JobPosition.query.get_or_404(id)
    
    # Counting views for job once per student per session 
    # Initialize 'viewed_jobs' list in session if it doesn't exist
    if 'viewed_jobs' not in session:
        session['viewed_jobs'] = []

    # If this Job ID is not in the session's viewed list
    # We cast to list because session objects can be finicky with appends
    viewed_list = list(session['viewed_jobs']) 
    
    if id not in viewed_list:
        # Increment the existing column
        job.views = (job.views or 0) + 1
        
        # Add to session so they aren't counted again this session
        viewed_list.append(id)
        session['viewed_jobs'] = viewed_list 
        db.session.commit()
    return render_template('student/view_job.html', 
                            job=job, 
                            user=current_user,
                            active_page='job_postings')


# --- ACTION: JOB APPLY ---
@student_bp.route('/job/apply/<int:id>', methods=['GET', 'POST'])
@student_required
def apply_job(id):

    student = current_user.student_details
    job = JobPosition.query.get_or_404(id)
    
    # CHECK DUPLICATE APPLICATION
    # We check if this student has already applied to this specific job_position_id
    existing_app = Application.query.filter_by(
        student_id=student.id, 
        job_position_id=job.id
    ).first()

    if existing_app:
        flash(f'You have already applied for the {job.job_title} position.', 'warning')
        return redirect(url_for('student_bp.job_postings'))

    if request.method == 'POST':
        try:
            cover_letter_text = request.form.get('cover_letter')

            resume = None 
            if 'resume' in request.files:
                file = request.files['resume']
                if file and file.filename != '':
                    filename = os.path.basename(file.filename) 
                    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'Resumes' , filename)
                    file.save(save_path)

                    resume = f"/static/uploads/Resumes/{filename}"

            # Application Entry
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
        
    return render_template('student/apply_job.html', 
                            user=current_user, 
                            job=job)
    


# --- APPLICATIONS ROUTE ---
@student_bp.route('/applications')
@student_required
def applications():

    # Join Job -> Company -> User (to get Company Name & Logo)
    my_id = current_user.student_details.id
    
    query = Application.query.join(JobPosition).join(Company).join(User)
    
    # SEARCH LOGIC
    search_query = request.args.get('q', '')
    status_filter = request.args.get('status', '')
    if search_query:
        search = f"%{search_query}%"
        query = query.filter(
                (JobPosition.job_title.ilike(search)) |   # Job Title
                (User.name.ilike(search))                # Company Name    
        )
        
    if status_filter:
        query = query.filter(Application.application_status == status_filter)

    all_applications = query.filter(Application.student_id == my_id).order_by(Application.applied_at.desc()).all()

    return render_template('student/applications.html', 
                            user=current_user,
                            search=search_query,
                            status=status_filter,
                            applications = all_applications)
    

# --- ACTION: VIEW JOB OFFER ---
@student_bp.route('/offer/view/<int:id>')
@student_required
def view_offer(id):

    application = Application.query.get_or_404(id)
    
    return render_template('student/view_offer.html', 
                            application=application, 
                            user=current_user)

    
# --- ACTION: JOIN OFFER ---
@student_bp.route('/offer/join/<int:id>')
def join_offer(id):

    application = Application.query.get_or_404(id)
    
    try:
        application.placements.status = 'Joined'
        db.session.commit()
        
        flash(f'Congratulations! You have successfully accepted the offer at {application.job_position.company.user.name}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while processing your request.', 'danger')

    return redirect(url_for('student_bp.applications'))


# --- ACTION: DECLINE OFFER ---
@student_bp.route('/offer/decline/<int:id>')
def decline_offer(id):

    application = Application.query.get_or_404(id)

    try:
        application.placements.status = 'Declined'
        db.session.commit()
        
        flash('You have declined the offer.', 'info')
    except Exception as e:
        db.session.rollback()
        flash('Error processing request.', 'danger')

    return redirect(url_for('student_bp.applications'))
        


# --- HELPER: GENERATE PROFESSIONAL MESSAGES ---
def get_status_message(application):
    status = application.application_status
    company_name = application.job_position.company.user.name
    role = application.job_position.job_title
    
    if status == 'Applied':
        return {
            "title": "Application Received",
            "heading": "Thanks for applying!",
            "body": f"We have received your application for the {role} position at {company_name}. Our HR team is currently reviewing your profile to see if it matches our requirements. We appreciate your interest and will update you as soon as we move to the next stage.",
            "action": "View Application",
            "class": "warning"
        }
    elif status == 'Shortlisted':
        return {
            "title": "Profile Shortlisted",
            "heading": "Great News! You're on our radar.",
            "body": f"Your profile stood out to us for the {role} role. We have shortlisted your application for further review. This is a positive step! Please keep an eye on your notifications for interview schedules or further instructions.",
            "action": "Prepare for Interview",
            "class": "info"
        }
    elif status == 'Selected':
        # Check if placement details exist (assuming you might add remarks in Placement later)
        return {
            "title": "Congratulations! You're Hired.",
            "heading": "Welcome to the team!",
            "body": f"We are thrilled to offer you the position of {role} at {company_name}. Your skills and experience are exactly what we were looking for. Please find your offer letter details below.",
            "action": "Download Offer Letter",
            "class": "success"
        }
    elif status == 'Rejected':
        # Default motivating message if no specific remark exists
        return {
            "title": "Rejected",
            "heading": "Thank you for your effort.",
            "body": f"Thank you for giving us the opportunity to review your profile for the {role} position. While we were impressed with your credentials, we have decided to move forward with other candidates who are a closer fit for our specific needs at this time. Please do not be discouraged; we encourage you to apply for future openings.",
            "action": "Browse More Jobs",
            "class": "danger"
        }
    else:
        return {
            "title": "Status Update",
            "heading": "Update on your application",
            "body": "Your application status has been updated.",
            "class": "secondary"
        }

# --- NOTIFICATIONS LIST  ---
@student_bp.route('/notifications')
@student_required
def notifications():

    student = current_user.student_details
    
    query = Application.query
    status_filter = request.args.get('status', '')
    if status_filter:
        query = query.filter(Application.application_status == status_filter)
    
    # (Newest first)
    my_apps = query.filter(Application.student_id==student.id , Application.is_cleared == False).order_by(Application.applied_at.desc()).all()
    
    return render_template('student/notifications.html', 
                            user=current_user,
                            applications=my_apps,
                            status=status_filter)


# --- VIEW NOTIFICATION (Detailed Message) ---
@student_bp.route('/notification/view/<int:id>')
@student_required
def view_notification(id):

    application = Application.query.get_or_404(id)
    
    # Security: EnsurING student owns this notification
    if application.student.user.id != current_user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('student_bp.notifications'))

    # GeneratING the custom message based on current status
    message_data = get_status_message(application)
    application.is_read = True
    db.session.commit()

    return render_template('student/view_notification.html', 
                            user=User.query.get(current_user.id),
                            application=application,
                            msg=message_data)


# --- ACTION: CLEAR SINGLE NOTIFICATION ---
@student_bp.route('/notification/clear/<int:id>')
@student_required
def clear_notification(id):
    app = Application.query.get_or_404(id)
    # Check ownership
    if app.student.user.id == current_user.id:
        app.is_cleared = True  
        db.session.commit()
    return redirect(url_for('student_bp.notifications'))


# --- ACTION: CLEAR ALL NOTIFICATIONS ---
@student_bp.route('/notifications/clear_all')
@student_required
def clear_all_notifications():
    user_id = current_user.id
    student = User.query.get(user_id).student_details
    
    # Bulk update
    Application.query.filter_by(student_id=student.id).update(dict(is_cleared=True))
    db.session.commit()
    
    flash("All notifications cleared.", "success")
    return redirect(url_for('student_bp.notifications'))


# --- PLACEMENT HISTORY ROUTE ---
@student_bp.route('/history')
def history():

    if not current_user.student_details:
        flash('Please complete your profile first.', 'info')
        return redirect(url_for('student_bp.setup'))
    
    my_id = current_user.student_details.id
    
    query = Placement.query.join(Application)
    
    status_filter = request.args.get('status', '')
        
    if status_filter:
        query = query.filter(Placement.status == status_filter)

    placements = query.filter(Application.student_id == my_id , Placement.status != "Offered").order_by(Placement.created_at.desc()).all()
    return render_template('student/history.html' , placements=placements, user=current_user, status=status_filter)
