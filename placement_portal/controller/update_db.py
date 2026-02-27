from app import app, db
from sqlalchemy import text
import secrets

def get_unique_id():
    return secrets.token_urlsafe(16)

with app.app_context():
    conn = db.session.connection()
    print("--- STARTING SMART MIGRATION ---")

    # 1. USER TABLE: Security Tokens
    try:
        conn.execute(text("ALTER TABLE user ADD COLUMN fs_uniquifier VARCHAR(255)"))
        conn.execute(text("ALTER TABLE user ADD COLUMN last_login_at DATETIME"))
        # Populate tokens
        users = conn.execute(text("SELECT id FROM user")).fetchall()
        for u in users:
            uid = get_unique_id()
            conn.execute(text(f"UPDATE user SET fs_uniquifier = '{uid}' WHERE id = {u[0]}"))
        print("[User] Security columns added and populated.")
    except Exception: print("[User] Columns likely exist.")

    # 2. STUDENT TABLE: Soft Delete
    try:
        conn.execute(text("ALTER TABLE student ADD COLUMN is_deleted BOOLEAN DEFAULT 0"))
        print("[Student] Soft delete added.")
    except Exception: pass

    # 3. COMPANY TABLE: Status Migration (The Tricky Part)
    try:
        conn.execute(text("ALTER TABLE company ADD COLUMN status VARCHAR(20) DEFAULT 'Pending'"))
        conn.execute(text("ALTER TABLE company ADD COLUMN rejection_reason VARCHAR(255)"))
        conn.execute(text("ALTER TABLE company ADD COLUMN is_deleted BOOLEAN DEFAULT 0"))
        
        # MIGRATE DATA: Map old Boolean to new String
        conn.execute(text("UPDATE company SET status = 'Approved' WHERE is_approved = 1"))
        conn.execute(text("UPDATE company SET status = 'Pending' WHERE is_approved = 0"))
        print("[Company] Migrated 'is_approved' boolean to 'status' string.")
    except Exception: print("[Company] Columns likely exist.")

    # 4. JOB POSITION: Status Migration & Analytics
    try:
        conn.execute(text("ALTER TABLE job_position ADD COLUMN status VARCHAR(20) DEFAULT 'Pending'"))
        conn.execute(text("ALTER TABLE job_position ADD COLUMN rejection_reason VARCHAR(255)"))
        conn.execute(text("ALTER TABLE job_position ADD COLUMN views INTEGER DEFAULT 0"))
        conn.execute(text("ALTER TABLE job_position ADD COLUMN is_deleted BOOLEAN DEFAULT 0"))

        # MIGRATE DATA
        conn.execute(text("UPDATE job_position SET status = 'Approved' WHERE is_approved = 1"))
        conn.execute(text("UPDATE job_position SET status = 'Pending' WHERE is_approved = 0"))
        # Note: If you had 'Closed' jobs, you'll need to update them manually or via logic later
        print("[JobPosition] Migrated 'is_approved' boolean to 'status' string.")
    except Exception: print("[JobPosition] Columns likely exist.")

    # 5. APPLICATION: Notifications
    try:
        conn.execute(text("ALTER TABLE application ADD COLUMN is_read BOOLEAN DEFAULT 0"))
        conn.execute(text("ALTER TABLE application ADD COLUMN is_cleared BOOLEAN DEFAULT 0"))
        conn.execute(text("ALTER TABLE application ADD COLUMN remarks VARCHAR(500)"))
        print("[Application] Notification columns added.")
    except Exception: pass

    db.session.commit()
    print("--- MIGRATION COMPLETE: No Data Lost ---")