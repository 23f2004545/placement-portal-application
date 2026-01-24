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
        if current_user.student_details:
            return render_template('student/profile.html' , user=current_user)
        return render_template('student/edit.html' , user=current_user)
    else :
        flash('Unauthorized access', 'danger')
        return redirect(url_for('auth_bp.login'))

    if request.method == 'POST':
        try:
            current_user.name = request.form.get('name')
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
            student.cgpa = float(request.form.get('cgpa'))
            student.experience = int(request.form.get('experience'))
            student.skill_set = request.form.get('skill_set')
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
            return render_template('student/profile.html' , user=current_user)

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')
            return render_template('student/edit.html')
        
    return render_template('student/edit.html', user=current_user)
