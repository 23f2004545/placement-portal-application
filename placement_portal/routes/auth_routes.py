from flask import Blueprint ,current_app , render_template , request , session , flash , redirect , url_for
from controller.models import *
import os 

auth_bp = Blueprint('auth_bp', __name__) 

@auth_bp.route("/login" , methods=['GET','POST'])
def login():
    if request.method == 'GET':
        if 'user_id' in session:
            role = session['role']
            return redirect(url_for(f"{role}_bp.profile"))  
        return render_template('auth/login.html')
    
    if request.method == 'POST':
        email = request.form.get('email', None)
        password = request.form.get('password' , None)
        
        #existence of user 
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('Incorrect email or password', 'warning')
            return redirect(url_for('auth_bp.login'))
        else:
            if user.password == password:
                session['user_id'] = user.id
                session['role'] = user.roles.name
                role = session['role']
                flash('Login successful', 'success')
                return redirect(url_for(f"{role}_bp.profile"))  
            else: 
                flash('Incorrect email or password', 'warning')
                return redirect(url_for('auth_bp.login'))
        
        
@auth_bp.route('/logout')
def logout():
    if "user_id" not in session:
        flash('You are not logged in', 'warning')
        return redirect(url_for('auth_bp.login'))
    else :
        session.pop('user_id')
        session.pop('role')
        flash('You are logged out', 'warning')
        return redirect(url_for('auth_bp.login'))
    
    
@auth_bp.route("/register" , methods=['GET','POST'])
def register():
    if request.method == 'GET':
        if 'user_id' in session:
            role = session['role']
            return redirect(url_for(f"{role}"))
        return render_template('auth/register.html')   

    if request.method == 'POST':
        name = request.form.get('name', None)
        email = request.form.get('email', None)
        password = request.form.get('password' , None)
        contact = request.form.get('contact' , None)
        role = request.form.get('role' , None)
        
        profile_pic = None 
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename != '':
                filename = os.path.basename(file.filename) # Prevents directory traversal
                save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'Profile_pics' , filename)
                file.save(save_path)

                profile_pic = f"/static/uploads/Profile_pics/{filename}"
        # Fallback if no image uploaded
        if not profile_pic :
            profile_pic = f"/static/uploads/Profile_pics/{role}.png"
            
        
        name = name.strip().title() 
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'warning')
            return redirect(url_for('auth_bp.register'))

        user = User.query.filter_by(email=email).first()
        if user:        
            flash('User already exists', 'danger')
            return redirect(url_for('auth_bp.register'))
        
        role = Role.query.filter_by(name=role).first()
        user = User(
            name=name , 
            email=email , 
            password=password , 
            contact=contact , 
            image_url=profile_pic , 
            roles=role 
            )
        
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('auth_bp.login'))
        