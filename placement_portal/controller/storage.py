import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename

def upload_file(file, folder_name="general"):
    """
    Uploads a file to Cloudinary if configured; otherwise saves to local disk.
    Returns the URL string to store in the database.
    """
    if not file or file.filename == '':
        return None

    # 1. Try Cloudinary if CLOUDINARY_URL is configured
    cloudinary_url = current_app.config.get('CLOUDINARY_URL')
    if cloudinary_url:
        try:
            import cloudinary
            import cloudinary.uploader
            
            # Use raw for PDFs and documents, auto for images/videos
            is_pdf = file.filename.lower().endswith('.pdf')
            res_type = "raw" if is_pdf else "auto"
            
            upload_result = cloudinary.uploader.upload(
                file,
                folder=f"placement_portal/{folder_name}",
                resource_type=res_type
            )
            return upload_result.get("secure_url")
        except Exception as e:
            current_app.logger.warning(f"Cloudinary upload failed: {e}. Falling back to local storage.")

    # 2. Local Storage Fallback
    original_filename = secure_filename(file.filename)
    extension = os.path.splitext(original_filename)[1]
    unique_prefix = uuid.uuid4().hex[:10]
    
    if original_filename:
        unique_filename = f"{unique_prefix}_{original_filename}"
    else:
        unique_filename = f"{unique_prefix}{extension}"

    target_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], folder_name)
    os.makedirs(target_dir, exist_ok=True)

    file_path = os.path.join(target_dir, unique_filename)
    file.seek(0)
    if hasattr(file, 'save'):
        file.save(file_path)
    else:
        with open(file_path, 'wb') as f:
            f.write(file.read())

    return f"/static/uploads/{folder_name}/{unique_filename}"
