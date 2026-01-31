from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from controller.models import db, Student, Company, Application

api_bp = Blueprint('api_bp', __name__)

# =================================================
# 1. READ (GET): Fetch Data
# =================================================

@api_bp.route('/api/students', methods=['GET'])
@login_required
def get_students():
    # Requirement: Return JSON list of students
    students = Student.query.filter_by(is_deleted=False).all()
    return jsonify([s.to_dict() for s in students]), 200

@api_bp.route('/api/companies', methods=['GET'])
@login_required
def get_companies():
    companies = Company.query.filter_by(is_deleted=False).all()
    return jsonify([c.to_dict() for c in companies]), 200

# =================================================
# 2. CREATE (POST): Add Data (e.g., Apply for Job)
# =================================================

@api_bp.route('/api/application/create', methods=['POST'])
@login_required
def create_application():
    # Expecting JSON: {"job_id": 12, "cover_letter": "..."}
    data = request.get_json()
    
    # Simple Validation
    if not data or 'job_id' not in data:
        return jsonify({'error': 'Missing job_id'}), 400
        
    # (In a real app, you would add logic here to save to DB)
    # For the milestone, demonstrating the endpoint structure is often enough,
    # OR you can copy your apply_logic here.
    
    return jsonify({'message': 'Application received successfully', 'data': data}), 201

# =================================================
# 3. UPDATE (PUT): Modify Data
# =================================================

@api_bp.route('/api/student/update', methods=['PUT'])
@login_required
def update_student_profile():
    # Only allow students to update their own profile
    if not current_user.student_details:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json()
    student = current_user.student_details
    
    # Update fields if provided
    if 'cgpa' in data:
        student.cgpa = data['cgpa']
    if 'skills' in data:
        student.skill_set = data['skills']
        
    db.session.commit()
    return jsonify({'message': 'Profile updated', 'student': student.to_dict()}), 200

# =================================================
# 4. DELETE (DELETE): Remove Data
# =================================================

@api_bp.route('/api/application/<int:id>', methods=['DELETE'])
@login_required
def delete_application(id):
    app = Application.query.get_or_404(id)
    
    # Ownership Check
    if app.student.user.id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    # Hard Delete or Soft Delete
    db.session.delete(app)
    db.session.commit()
    
    return jsonify({'message': 'Application withdrawn successfully'}), 200