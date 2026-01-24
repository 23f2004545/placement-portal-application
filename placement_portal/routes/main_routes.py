from app import app
from flask import  render_template , session , flash , redirect , url_for

@app.route('/')
def home():
    if 'user_id' in session:
        role = session['role']
        return redirect(url_for(f"{role}_bp.dashboard"))
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