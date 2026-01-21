from app import app
from flask import render_template , session , flash , redirect , url_for
from controller.models import *

@app.route('/admin')
def admin():
    if not session.get('user_id', None):
        return redirect(url_for('login'))  
    elif session.get('role') == 'admin':
            return render_template('admin/dashboard.html')
    else:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))
    