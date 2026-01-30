from app import app
from flask import  render_template , session , flash , redirect , url_for
from controller.db import db
from controller.models import User,Application
from datetime import datetime , timezone

@app.route('/')
def home():
    if 'user_id' in session:
        role = session['role']
        return redirect(url_for(f"{role}_bp.profile"))
    return render_template('auth/login.html')


# ERROR HANDLERS
@app.errorhandler(404)
def page_not_found(e):
    #"404" at the end, tells the browser it's actually an error.
    return render_template('404.html'), 404   # Handle 404 (Page Not Found)

@app.errorhandler(500)
def internal_server_error(e):  
    return render_template('404.html'), 500   # Handle 500 (Internal Server Error)

@app.errorhandler(405)
def method_not_allowed(e):
    flash('Invalid request method.', 'danger')
    return redirect(url_for('auth_bp.login'))  # Handle 405 (Method Not Allowed)


@app.context_processor
def inject_notifications():
    if session.get('role') == 'student':
        user_id = session['user_id']
        current_user = User.query.get(user_id)
        if current_user and current_user.student_details:
            # Count apps that are NOT cleared and NOT read
            count = Application.query.filter_by(
                student_id=current_user.student_details.id ,
                is_read=False,
                is_cleared=False 
                ).count()
            return dict(unread_count=count)
    return dict(unread_count=0)


# Last login management
@app.template_filter('time_ago')
def time_ago_filter(value):
    if not value:
        return "Never"

    # 1. Get the current UTC time
    # 2. .replace(tzinfo=None) makes it "naive" to match your DB
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    diff = now - value
    
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "Just now"
        if second_diff < 60:
            return f"{second_diff} seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return f"{second_diff // 60} minutes ago"
        if second_diff < 7200:
            return "a hour ago"
        if second_diff < 86400:
            return f"{second_diff // 3600} hours ago"
    
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return f"{day_diff} days ago"
    if day_diff < 31:
        return f"{day_diff // 7} weeks ago"
    if day_diff < 365:
        return f"{day_diff // 30} months ago"
    
    return f"{day_diff // 365} years ago"