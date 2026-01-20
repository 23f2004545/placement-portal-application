from app import app
from flask import render_template , request , session , flash , redirect , url_for
from controller.models import *

@app.route('/login' , methods=['GET','POST'])
def login():
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect(url_for('home'))  #redirect to assigned role's dashboard
        return render_template('auth/login.html')
    
    if request.method == 'POST':
        email = request.form.get('email', None)
        password = request.form.get('password' , None)
        
        #existence of user 
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('Incorrect email or password', 'warning')
            return redirect('/login')
        else:
            if user.password == password:
                session['user_id'] = user.id
                session['role'] = user.roles.name
                flash('Login successful', 'success')
                return redirect(url_for('home'))  #redirect to assigned role's dashboard
            else: 
                flash('Incorrect email or password', 'warning')
                return redirect('/login')
        
        
@app.route('/logout')
def logout():
    if "user_id" not in session:
        flash('You are not logged in', 'warning')
        return redirect('/login')
    else :
        session.pop('user_id')
        session.pop('role')
        flash('You are logged out', 'warning')
        return redirect('/login')
    
    
@app.route('/register' , methods=['GET','POST'])
def register():
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect(url_for('home'))
        return render_template('auth/register.html')   

    if request.method == 'POST':
        name = request.form.get('name', None)
        email = request.form.get('email', None)
        password = request.form.get('password' , None)
        contact = request.form.get('contact' , None)
        role = request.form.get('role' , None)
        profile_pic = request.form.get('profile_pic') or f"https://api.dicebear.com/7.x/identicon/svg?seed={name}"

        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'warning')
            return redirect('/register')

        user = User.query.filter_by(email=email).first()
        if user:        
            flash('User already exists', 'danger')
            return redirect('/register')
        
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
        return redirect('/login')
        