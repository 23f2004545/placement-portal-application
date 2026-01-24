from flask import Blueprint , current_app , render_template , session , flash , redirect , url_for
from controller.models import *

admin_bp = Blueprint('admin_bp', __name__) 

@admin_bp.route('/profile')
def profile():
    if not session.get('user_id', None):
        return redirect(url_for('auth_bp.login'))  
    elif session.get('role') == 'admin':
        return render_template('admin/profile.html')
    else:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('auth_bp.login'))
    