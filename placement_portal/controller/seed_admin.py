from app import app
from controller.db import db
from controller.models import User , Role
from werkzeug.security import generate_password_hash

def seed_admin():
    with app.app_context():
        admin = User.query.filter_by(name="admin").first()

        if admin:
            print("Admin already exists. Skipping seeding.")
            return

        else:
            admin_role = Role.query.filter_by(name='admin').first()
            admin = User(
                name="admin", 
                email="admin@gmail.com", 
                password=generate_password_hash("admin123"), 
                contact="7898789078", 
                image_url="https//admin_image",
                roles=admin_role)

        db.session.add(admin)
        db.session.commit()

        print("Admin user created successfully.")
        

if __name__ == "__main__":
    seed_admin()
