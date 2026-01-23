from flask import Blueprint , current_app , render_template , session , flash , redirect , url_for , request
from controller.models import *
import os

student_bp = Blueprint('student_bp', __name__) 

@student_bp.route('/dashboard')
def dashboard():
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))
    elif session.get('role') == 'student':
        user_id = session['user_id']
        current_user = User.query.filter_by(id=user_id).first()
        if not current_user.student_details:
            flash('Please complete your profile first.', 'info')
            return redirect(url_for('student_bp.setup'))
        return render_template('student/dashboard.html' , user=current_user)
    else:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('auth_bp.login'))
    
    
@student_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'GET':
        if not session.get('user_id', None):
            return redirect(url_for('auth_bp.login'))    
        elif session.get('role') == 'student':
            user_id = session['user_id']
            current_user = User.query.filter_by(id=user_id).first()
            if current_user.student_details:
                return render_template('student/dashboard.html' , user=current_user)
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
        
        flash('Profile Completed! Welcome to your Dashboard.', 'success')
        return redirect(url_for('student_bp.dashboard'))

    return render_template('student/setup.html')