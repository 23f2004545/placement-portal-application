from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from controller.models import db, Student, Company, Application

api_bp = Blueprint('api_bp', __name__)

# =================================================
# 1. READ (GET): Fetch Data
# =================================================

@api_bp.route('/students', methods=['GET'])
@login_required
def get_students():
    # Only Admin, Company recruiters, or the student themselves should access student lists
    user_role = getattr(current_user.roles, 'name', None)
    if user_role not in ['admin', 'company']:
        if current_user.student_details:
            return jsonify([current_user.student_details.to_dict()]), 200
        return jsonify({'error': 'Unauthorized'}), 403

    students = Student.query.filter_by(is_deleted=False).all()
    return jsonify([s.to_dict() for s in students]), 200

@api_bp.route('/companies', methods=['GET'])
@login_required
def get_companies():
    companies = Company.query.filter_by(is_deleted=False).all()
    return jsonify([c.to_dict() for c in companies]), 200

# =================================================
# 2. CREATE (POST): Add Data (e.g., Apply for Job)
# =================================================

@api_bp.route('/application/create', methods=['POST'])
@login_required
def create_application():
    data = request.get_json()

    if not data or 'job_id' not in data:
        return jsonify({'error': 'Missing job_id'}), 400
        
    return jsonify({'message': 'Application received successfully', 'data': data}), 201

# =================================================
# 3. UPDATE (PUT): Modify Data
# =================================================

@api_bp.route('/student/update', methods=['PUT'])
@login_required
def update_student_profile():
    if not current_user.student_details:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON body'}), 400

    student = current_user.student_details
    
    if 'cgpa' in data:
        try:
            val = float(data['cgpa'])
            if 0.0 <= val <= 10.0:
                student.cgpa = val
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid CGPA value'}), 400

    if 'skills' in data and isinstance(data['skills'], str):
        student.skill_set = data['skills'].strip()
        
    db.session.commit()
    return jsonify({'message': 'Profile updated', 'student': student.to_dict()}), 200

# =================================================
# 4. DELETE (DELETE): Remove Data
# =================================================

@api_bp.route('/application/<int:id>', methods=['DELETE'])
@login_required
def delete_application(id):
    app = Application.query.get_or_404(id)
    
    # Ownership Check
    if app.student.user.id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    db.session.delete(app)
    db.session.commit()
    
    return jsonify({'message': 'Application withdrawn successfully'}), 200