from flask import flash, redirect, url_for
from flask_login import current_user
from functools import wraps

# Admin decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        
        if not current_user.is_authenticated:
            flash("Login required", "warning")
            return redirect(url_for('auth_bp.login'))
        
        if current_user.roles.name != "admin":
            flash("Unauthorized access.", "danger")
            return redirect(url_for('auth_bp.login'))
            
        return f(*args, **kwargs)
    return decorated_function



# Company decorator
def company_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        
        if not current_user.is_authenticated:
            flash("Login required", "warning")
            return redirect(url_for('auth_bp.login'))
        
        if current_user.roles.name != "company":
            flash("Unauthorized access.", "danger")
            return redirect(url_for('auth_bp.login'))

        if not current_user.company_details:
            flash('Please complete your profile first.', 'info')
            return redirect(url_for('company_bp.setup'))

        company = current_user.company_details
        
        if company.status != 'Approved':
            return redirect(url_for('company_bp.verification'))
        
        if company.is_deleted:
            from flask_login import logout_user
            logout_user() 
            flash("Account deactivated.", "danger")
            return redirect(url_for('auth_bp.login'))
            
        return f(*args, **kwargs)
    return decorated_function



# Student decorator
def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        
        if not current_user.is_authenticated:
            flash("Login required", "warning")
            return redirect(url_for('auth_bp.login'))
        
        if current_user.roles.name != "student":
            flash("Unauthorized access.", "danger")
            return redirect(url_for('auth_bp.login'))

        if not current_user.student_details:
            flash('Please complete your profile first.', 'info')
            return redirect(url_for('company_bp.setup'))

        student = current_user.student_details
        
        if student.is_deleted:
            from flask_login import logout_user
            logout_user() 
            flash("Account deactivated.", "danger")
            return redirect(url_for('auth_bp.login'))
            

        return f(*args, **kwargs)
    return decorated_function