from flask import Blueprint , current_app , render_template , session , flash , redirect , url_for , request
from controller.models import *

company_bp = Blueprint('company_bp', __name__) 

@company_bp.route('/dashboard')
def dashboard():
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))   
    elif session.get('role') == 'company':
        user_id = session['user_id']
        current_user = User.query.filter_by(id=user_id).first()
        if not current_user.company_details:
            flash('Please complete your profile first.', 'info')
            return redirect(url_for('company_bp.setup'))
        if current_user.company_details.is_approved == False:
            return redirect(url_for('company_bp.verification'))
        return render_template('company/dashboard.html' , user=current_user)
    else:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('auth_bp.login'))
    
@company_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'GET':
        if not session.get('user_id', None):
            return redirect(url_for('auth_bp.login'))    
        elif session.get('role') == 'company':
            user_id = session['user_id']
            current_user = User.query.filter_by(id=user_id).first()
            if current_user.company_details:
                return render_template('company/dashboard.html' , user=current_user)
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
    if not session.get('user_id', None):
            return redirect(url_for('auth_bp.login'))    
    elif session.get('role') == 'company':
        user_id = session['user_id']
        current_user = User.query.filter_by(id=user_id).first()
        if current_user.company_details and current_user.company_details.is_approved:
            flash('Your account is already approved!', 'success')
            return render_template('company/dashboard.html' , user=current_user)
        return render_template('company/wait.html' , user=current_user)
    else :
        flash('Unauthorized access', 'danger')
        return redirect(url_for('auth_bp.login'))