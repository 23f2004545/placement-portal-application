from app import app
from flask import render_template , session , flash , redirect , url_for
from controller.models import *

@app.route('/company')
def company():
    if not session.get('user_id', None):
        return redirect(url_for('login'))   
    elif session.get('role') == 'company':
            return render_template('company/dashboard.html')
    else:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))