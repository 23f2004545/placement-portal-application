import os

# Optionally load .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "secret_key_dev_default")
    
    # Read cloud database URL, falling back to local SQLite
    database_url = os.environ.get("DATABASE_URL", "sqlite:///database.sqlite3")
    
    # Render / Supabase compatibility: SQLAlchemy requires postgresql:// instead of legacy postgres://
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Use absolute path for upload folder to prevent path issues across different working directories
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(BASE_DIR, "static/uploads"))
    
    # Cloudinary Cloud Storage (Optional - falls back to local storage if not set)
    CLOUDINARY_URL = os.environ.get("CLOUDINARY_URL", None)