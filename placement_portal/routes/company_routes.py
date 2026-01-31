from flask import Blueprint , current_app , render_template , flash , redirect , url_for , request
from controller.decorators import company_required
from flask_login import current_user
from controller.models import *
import os

company_bp = Blueprint('company_bp', __name__) 

@company_bp.route('/profile')
@company_required
def profile():  
    
    my_jobs = JobPosition.query.filter_by(company_id=current_user.company_details.id, job_status='Hiring').all()
    
    # List Comprehension to extract data
    # Label: Job Title (e.g., "Python Dev")
    # Value: Count of applications for that job
    job_labels = [job.job_title for job in my_jobs]
    app_counts = [len(job.applications) for job in my_jobs]

    return render_template('company/profile.html' ,
                           user=current_user ,
                           job_labels=job_labels,
                           app_counts=app_counts)

    
# --- ACTION: ACCOUNT SETUP ---
@company_bp.route('/setup', methods=['GET', 'POST'])
@company_required
def setup():

    if request.method == 'POST':
        if current_user.company_details and current_user.company_details.status == "Rejected":
            hr_name = request.form.get('hr_name')
            employee_count = request.form.get('employee_count')
            location = request.form.get('location')
            website = request.form.get('website') 
            description = request.form.get('description')

            if not all([hr_name, employee_count, location, website]):
                flash("All fields are required.", "warning")
                return redirect(url_for('student_bp.edit_profile'))

            if not hr_name.replace(" ", "").isalpha():
                flash("Name must contain only alphabetic characters and spaces.", "warning")
                return redirect(url_for('student_bp.edit_profile'))

            if employee_count < 0:
                flash("Employee count can't be negative.", "warning")
                return redirect(url_for('student_bp.edit_profile'))
            
            current_user.company_details.user_id=user_id 
            current_user.company_details.hr_name=hr_name.strip().title() 
            current_user.company_details.employee_count=employee_count
            current_user.company_details.location=location.strip().title()
            current_user.company_details.website=website
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
            
            if not all([hr_name, employee_count, location, website]):
                flash("All fields are required.", "warning")
                return redirect(url_for('student_bp.edit_profile'))

            if not hr_name.replace(" ", "").isalpha():
                flash("Name must contain only alphabetic characters and spaces.", "warning")
                return redirect(url_for('student_bp.edit_profile'))

            if employee_count < 0:
                flash("Employee count can't be negative.", "warning")
                return redirect(url_for('student_bp.edit_profile'))
            
            hr_name = hr_name.strip().title()        
            location = location.strip().title()        
            # --- CREATE company RECORD ---
            user_id = current_user.id
            new_company = Company(
                user_id=user_id, 
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

    if current_user.company_details:
        return render_template('company/profile.html' , user=current_user)
    return render_template('company/setup.html' , user=current_user)


# --- THE WAITING ROOM ROUTE ---
@company_bp.route('/verification')
@company_required
def verification():

    if current_user.company_details.status == "Approved":
        flash('Your account is already approved!', 'success')
        return render_template('company/profile.html' , user=current_user)
    if current_user.company_details.status == "Rejected" :
        flash('Your company profile was rejected. Please retry.', 'danger')
        return render_template('company/retry.html' , user=current_user)
    flash('Your company profile is under review. Please wait for approval.', 'info')
    return render_template('company/wait.html' , user=current_user)    

    
# --- ACTION: EDIT PROFILE ---
@company_bp.route('/profile/edit', methods=['GET', 'POST'])
@company_required
def edit_profile():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            contact = request.form.get('contact', '').strip()
            hr_name = request.form.get('hr_name', '').strip()
            location = request.form.get('location', '').strip()
            website = request.form.get('website', '').strip()
            description = request.form.get('description', '').strip()
            employee_count = request.form.get('employee_count', '').strip()

            if not all([name, contact, hr_name, location, website]):
                flash("All fields are required.", "warning")
                return redirect(url_for('company_bp.edit_profile'))

            if not name.replace(" ", "").isalpha():
                flash("Company name must contain only alphabets.", "warning")
                return redirect(url_for('company_bp.edit_profile'))

            if not hr_name.replace(" ", "").isalpha():
                flash("HR name must contain only alphabets.", "warning")
                return redirect(url_for('company_bp.edit_profile'))

            if not (contact.isdigit() and len(contact) == 10):
                flash("Contact number must be exactly 10 digits.", "warning")
                return redirect(url_for('company_bp.edit_profile'))
            
            if employee_count < 0:
                flash("Employee count can't be negative.", "warning")
                return redirect(url_for('student_bp.edit_profile'))

            # --- Update User Table ---
            current_user.name = name.title()
            current_user.contact = contact

            # 6. Profile Picture Size (< 2MB)
            if 'profile_pic' in request.files:
                pic = request.files['profile_pic']
                if pic and pic.filename != '':
                    pic.seek(0, os.SEEK_END)
                    if pic.tell() > 2 * 1024 * 1024:
                        flash("Profile picture must be less than 2 MB.", "warning")
                        return redirect(url_for('company_bp.edit_profile'))
                    pic.seek(0) # Reset pointer
                    
                    filename = os.path.basename(pic.filename)
                    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'Profile_pics', filename)
                    pic.save(save_path)
                    current_user.image_url = f"/static/uploads/Profile_pics/{filename}"

            # --- Update Company Table ---
            company = current_user.company_details
            company.hr_name = hr_name.title()
            company.location = location.title()
            company.website = website
            company.description = description
            company.employee_count = employee_count

            db.session.commit()
            flash('Company profile updated successfully!', 'success')
            return redirect(url_for('company_bp.profile'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')
            return render_template('company/edit.html', user=current_user)

    return render_template('company/edit.html', user=current_user)



# --- THE JOB_POSTINGS ROUTE ---
@company_bp.route('/job_postings')
@company_required
def job_postings():

    # Join Job -> Company with current user's id
    company_id = current_user.company_details.id
    query = JobPosition.query.filter_by(company_id=company_id)
    
    # SEARCH LOGIC
    search_query = request.args.get('q', '')
    if search_query:
        search = f"%{search_query}%"
        query = query.filter(
                (JobPosition.job_title.ilike(search)) |   # Job Title
                (JobPosition.job_status.ilike(search))   # Status (Hiring/Closed)
        )
    
    all_jobs = query.order_by(JobPosition.created_at.desc()).all()
    
    # SEPARATE LISTS
    pending_jobs = [job for job in all_jobs if job.status == "Pending"]
    active_jobs = [job for job in all_jobs if job.status == "Approved"]

    return render_template('company/job_postings.html', 
                            user=current_user,
                            pending_jobs=pending_jobs,
                            active_jobs=active_jobs,
                            search=search_query,
                            jobs = all_jobs)


# --- ACTION: VIEW JOB ---
@company_bp.route('/job/view/<int:id>')
@company_required
def view_job(id):

    job = JobPosition.query.get_or_404(id)
    return render_template('company/view_job.html', 
                            job=job,
                            user=current_user)


# --- ACTION: CLOSE JOB ---
@company_bp.route('/job/close/<int:id>')
@company_required
def close_job(id):  

    job = JobPosition.query.get_or_404(id)
    job.job_status = "Closed"
    db.session.commit()
    
    flash(f'Job "{job.job_title}" has been closed.', 'warning')     
    return redirect(url_for('company_bp.job_postings'))


# --- ACTION: REOPEN JOB ---
@company_bp.route('/job/reopen/<int:id>')
@company_required
def reopen_job(id):  
    
    job = JobPosition.query.get_or_404(id)
    job.job_status = "Hiring"
    db.session.commit()
    
    flash(f'Job "{job.job_title}" has been reopened.', 'success')     
    return redirect(url_for('company_bp.job_postings'))


# --- ACTION: CREATE JOB ---
@company_bp.route('/jobs/create', methods=['GET', 'POST'])
@company_required
def create_job():

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


# --- THE APPLICATIONS ROUTE ---
@company_bp.route('/applications')
@company_required
def applications():

    # Join Application -> JobPosition -> Filter by Company ID
    my_company_id = current_user.company_details.id
    
    query = Application.query.join(JobPosition).filter(
        JobPosition.company_id == my_company_id
    )

    # SEARCH & FILTER
    search_query = request.args.get('q', '')

    if search_query:
        search = f"%{search_query}%"
        # We need to join Student & User to search by applicant Name
        query = query.join(Student).join(User).filter(
            (User.name.ilike(search)) |               # Applicant Name
            (JobPosition.job_title.ilike(search))     # Job Title
        )

    # (Newest First)
    my_applications = query.filter(Application.application_status=="Applied").order_by(Application.applied_at.desc()).all()

    return render_template('company/applications.html', 
                            user=current_user,
                            applications=my_applications,
                            search=search_query)
    
    
# --- ACTION: SHORTLIST APPLICATION ---
@company_bp.route('/application/shortlist/<int:id>')
@company_required
def shortlist_application(id):  
   
    application = Application.query.get_or_404(id)
    application.application_status = "Shortlisted"
    application.is_cleared = False
    db.session.commit()
    
    flash(f'Application has been shortlisted.', 'info')     
    return redirect(url_for('company_bp.applications'))

    
# --- ACTION: REJECT APPLICATION ---
@company_bp.route('/application/reject/<int:id>', methods=['GET', 'POST'])
@company_required
def reject_application(id):  

    application = Application.query.get_or_404(id)
    if request.method == 'POST':
        try:
            application.application_status = "Rejected"
            application.is_cleared = False
            application.remarks = request.form.get('remarks')
            db.session.commit()
            
            flash(f'Application has been rejected.', 'danger')     
            return redirect(url_for('company_bp.reviewed')) 
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error rejecting student: {str(e)}', 'danger')
            return redirect(url_for('company_bp.reviewed', id=id))

    return render_template('company/rejection.html',
                            user=current_user, 
                            application=application)


        
# --- THE REVIEWED APPLICATIONS ROUTE ---
@company_bp.route('/reviewed')
@company_required
def reviewed():

    # Join Application -> JobPosition -> Filter by Company ID
    my_company_id = current_user.company_details.id
    
    query = Application.query.join(JobPosition).filter(
        JobPosition.company_id == my_company_id
    )

    # SEARCH & FILTER
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

    # (Newest First)
    my_applications = query.filter(Application.application_status!="Applied").order_by(Application.applied_at.desc()).all()

    return render_template('company/reviewed.html', 
                            user=current_user,
                            applications=my_applications,
                            search=search_query,
                            status=status_filter,
                            active_page='reviewed')


# --- ACTION: SELECT APPLICATION ---
@company_bp.route('/application/select/<int:id>', methods=['GET', 'POST'])
@company_required
def select_application(id):  

    application = Application.query.get_or_404(id)
    if request.method == 'POST':
        # Update Application Status
        application.application_status = "Selected"
        application.is_cleared = False # Keep in notifications
        
        offer_letter = None 
        if 'offer_letter' in request.files:
            file = request.files['offer_letter']
            if file and file.filename != '':
                file.seek(0, os.SEEK_END)
                if pic.tell() > 2 * 1024 * 1024:
                        flash("Profile picture must be less than 2 MB.", "warning")
                        return redirect(url_for('company_bp.edit_profile'))
                pic.seek(0) # Reset pointer
                
                filename = os.path.basename(file.filename) 
                save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'Offer_letters' , filename)
                file.save(save_path)

            offer_letter = f"/static/uploads/Offer_letters/{filename}"
            

        application.remarks=request.form.get('remarks')
        # Create Placement Record
        new_placement = Placement(
            application_id=application.id,
            salary_offered=request.form.get('salary_offered'),
            joining_date=request.form.get('joining_date'),
            offer_letter=offer_letter,
            status='Offered'
        )
        
        db.session.add(new_placement)
        db.session.commit()
        
        flash(f'Offer sent to {application.student.user.name}!', 'success')
        return redirect(url_for('company_bp.reviewed'))
    return render_template('company/selection.html', application=application, user=current_user,)


# --- ACTION: VIEW APPLICATION ---
@company_bp.route('/application/view/<int:id>')
@company_required
def view_application(id):

    application = Application.query.get_or_404(id)
    return render_template('company/view_application.html', 
                            application=application,
                            user=current_user,
                            active_page='job_postings')


    