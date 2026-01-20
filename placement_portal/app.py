from flask import Flask , render_template
from controller.db import db
from controller.models import *
from config import config

app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)

with app.app_context():
    db.create_all()

    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(name='admin')
        db.session.add(admin_role)
        
    student_role = Role.query.filter_by(name='student').first()
    if not student_role:
        student_role = Role(name='student')
        db.session.add(student_role)
        
    company_role = Role.query.filter_by(name='company').first()
    if not company_role:
        company_role = Role(name='company')
        db.session.add(company_role)
        
    db.session.commit()


@app.route('/')
def hello():
    return render_template('base.html')

@app.route('/login')
def login():
    return render_template('auth/login.html')

@app.route('/register')
def register():
    return render_template('auth/register.html')



if __name__ == '__main__':
    app.run(debug=True)