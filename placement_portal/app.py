from flask import Flask 
from controller.db import db
from controller.models import *
from config import config

from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.student_routes import student_bp
from routes.company_routes import company_bp


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

# REGISTER THE BLUEPRINT
# url_prefix='/student' means every route in student_bp gets '/student' added to front
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(student_bp, url_prefix='/student')
app.register_blueprint(company_bp, url_prefix='/company')


from routes.main_routes import *

if __name__ == '__main__':
    app.run(debug=True)