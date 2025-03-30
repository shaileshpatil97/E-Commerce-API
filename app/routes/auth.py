from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app.models.user import User
from app.utils.validators import validate_email, validate_password
from app.utils.error_handlers import handle_validation_error, handle_unauthorized_error

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate input
    if not validate_email(data.get('email')):
        return handle_validation_error('Invalid email format')
    if not validate_password(data.get('password')):
        return handle_validation_error('Password must be at least 8 characters long')
        
    # Check if user already exists
    if User.get_by_email(data['email']):
        return handle_validation_error('Email already registered')
        
    # Create new user
    user = User(
        name=data['name'],
        email=data['email'],
        password=data['password']
    )
    user.save()
    
    # Generate tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        'message': 'User registered successfully',
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Validate input
    if not validate_email(data.get('email')):
        return handle_validation_error('Invalid email format')
        
    # Check user credentials
    user = User.get_by_email(data['email'])
    if not user or not user.check_password(data['password']):
        return handle_unauthorized_error('Invalid email or password')
        
    # Generate tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'refresh_token': refresh_token
    })

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)
    
    return jsonify({
        'access_token': access_token
    })

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    
    if not user:
        return handle_unauthorized_error('User not found')
        
    return jsonify(user.to_dict())

@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_current_user():
    current_user_id = get_jwt_identity()
    user = User.find_by_id(request.db, current_user_id)
    
    if not user:
        return handle_validation_error('User not found')
    
    data = request.get_json()
    
    # Update user fields
    if 'name' in data:
        user.name = data['name']
    
    if 'email' in data:
        if not validate_email(data['email']):
            return handle_validation_error('Invalid email format')
        
        # Check if email is already taken
        existing_user = User.find_by_email(request.db, data['email'])
        if existing_user and existing_user.id != user.id:
            return handle_validation_error('Email already registered')
        
        user.email = data['email']
    
    if 'password' in data:
        if not validate_password(data['password']):
            return handle_validation_error('Password must be at least 8 characters long')
        user.password_hash = User.generate_password_hash(data['password'])
    
    user.save(request.db)
    
    return jsonify({
        'message': 'User updated successfully',
        'user': user.to_dict()
    }), 200 