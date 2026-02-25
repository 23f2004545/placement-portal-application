from flask import Blueprint ,current_app , render_template , request , flash , redirect , url_for
from flask_login import login_user, logout_user, login_required, current_user
from controller.models import *
import os , re
from werkzeug.security import generate_password_hash
from datetime import datetime , timezone

auth_bp = Blueprint('auth_bp', __name__) 

@auth_bp.route("/login", methods=['GET', 'POST'])
def login():

    if request.method == 'GET':
        if current_user.is_authenticated:
            role = current_user.roles.name
            return redirect(url_for(f"{role}_bp.profile"))  
        return render_template('auth/login.html')
    
    if request.method == 'POST':
        email = request.form.get('email', None)
        password = request.form.get('password', None)
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('Incorrect email or password', 'warning')
            return redirect(url_for('auth_bp.login'))
        else:
            if user.check_password(password):
                login_user(user)
                
                # Update last login
                user.last_login_at = datetime.now(timezone.utc)
                db.session.commit()
                
                role = user.roles.name
                return redirect(url_for(f"{role}_bp.profile"))  
            else: 
                flash('Incorrect email or password', 'warning')
                return redirect(url_for('auth_bp.login'))
        
        
@auth_bp.route('/logout')
@login_required 
def logout():
    logout_user()
    flash('You are logged out', 'warning')
    return redirect(url_for('auth_bp.login'))
    
    
@auth_bp.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        if current_user.is_authenticated:
            role = current_user.roles.name
            return redirect(url_for(f"{role}_bp.profile"))
        return render_template('auth/register.html')   

    if request.method == 'POST':
        name = request.form.get('name', None)
        email = request.form.get('email', None)
        password = request.form.get('password', None)
        contact = request.form.get('contact', None)
        role_name = request.form.get('role', None) 
        
        profile_pic = None 
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename != '':
                filename = os.path.basename(file.filename) 
                save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'Profile_pics', filename)
                file.save(save_path)

                profile_pic = f"/static/uploads/Profile_pics/{filename}"
        
        # Fallback if no image uploaded
        if not profile_pic:
            profile_pic = f"/static/uploads/Profile_pics/{role_name}.png"
            
        name = name.strip().title() 

        # BACKEND VALIDATION LAYER 
        if not name or not email or not password or not contact or not role_name:
            flash("All fields are required.", "danger")
            return redirect(url_for('auth_bp.register'))

        # Regex for standard email format
        pattern = r'^[\w\.-]+@[\w\.-]+$'
        if re.match(pattern, email) is  None:
            flash("Invalid email format.", "warning")
            return redirect(url_for('auth_bp.register'))
        
        if not name.replace(" ", "").isalpha():
            flash("Name must contain only alphabetic characters and spaces.", "warning")
            return redirect(url_for('auth_bp.register'))
        
        if not(contact.isdigit() and len(contact) == 10):
            flash("Contact number must be exactly 10 digits.", "warning")
            return redirect(url_for('auth_bp.register'))
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'warning')
            return redirect(url_for('auth_bp.register'))
        
        if role not in ['student', 'company']:
            flash('Invalid role selected', 'danger')
            return redirect(url_for('auth_bp.register'))

        user = User.query.filter_by(email=email).first()
        if user:        
            flash('User already exists', 'danger')
            return redirect(url_for('auth_bp.register'))
        
        role_obj = Role.query.filter_by(name=role_name).first()
        hashed_pw = generate_password_hash(password)
        
        user = User(
            name=name, 
            email=email, 
            password=hashed_pw, 
            contact=contact, 
            image_url=profile_pic, 
            roles=role_obj 
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('auth_bp.login'))
        