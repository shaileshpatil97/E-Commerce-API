from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.coupon import Coupon
from app.models.user import User
from app.utils.validators import validate_discount_value, validate_dates
from app.utils.error_handlers import handle_validation_error, handle_not_found_error, handle_unauthorized_error

coupons_bp = Blueprint('coupons', __name__)

@coupons_bp.route('/', methods=['GET'])
@jwt_required()
def get_coupons():
    user_id = get_jwt_identity()
    user = User.get_by_id(user_id)
    
    if not user.is_admin():
        return handle_unauthorized_error('Admin access required')
        
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    coupons = Coupon.find_all(page, per_page)
    total = Coupon.count_all()
    
    return jsonify({
        'coupons': [coupon.to_dict() for coupon in coupons],
        'total': total,
        'page': page,
        'per_page': per_page
    })

@coupons_bp.route('/<code>', methods=['GET'])
def get_coupon(code):
    coupon = Coupon.get_by_code(code)
    if not coupon:
        return handle_not_found_error('Coupon not found')
    return jsonify(coupon.to_dict())

@coupons_bp.route('/', methods=['POST'])
@jwt_required()
def create_coupon():
    user_id = get_jwt_identity()
    user = User.get_by_id(user_id)
    
    if not user.is_admin():
        return handle_unauthorized_error('Admin access required')
        
    data = request.get_json()
    
    # Validate input
    if not validate_discount_value(data.get('value'), data.get('type')):
        return handle_validation_error('Invalid discount value')
    if not validate_dates(data.get('start_date'), data.get('end_date')):
        return handle_validation_error('Invalid date range')
        
    coupon = Coupon(
        code=data['code'],
        description=data['description'],
        discount_type=data['type'],
        discount_value=data['value'],
        start_date=data['start_date'],
        end_date=data['end_date'],
        min_purchase=data.get('min_purchase', 0),
        max_discount=data.get('max_discount'),
        usage_limit=data.get('usage_limit'),
        is_active=data.get('is_active', True)
    )
    coupon.save()
    
    return jsonify(coupon.to_dict()), 201

@coupons_bp.route('/<code>', methods=['PUT'])
@jwt_required()
def update_coupon(code):
    user_id = get_jwt_identity()
    user = User.get_by_id(user_id)
    
    if not user.is_admin():
        return handle_unauthorized_error('Admin access required')
        
    coupon = Coupon.get_by_code(code)
    if not coupon:
        return handle_not_found_error('Coupon not found')
        
    data = request.get_json()
    
    # Validate input
    if 'value' in data and 'type' in data:
        if not validate_discount_value(data['value'], data['type']):
            return handle_validation_error('Invalid discount value')
    if 'start_date' in data and 'end_date' in data:
        if not validate_dates(data['start_date'], data['end_date']):
            return handle_validation_error('Invalid date range')
            
    # Update coupon
    for key, value in data.items():
        setattr(coupon, key, value)
    coupon.save()
    
    return jsonify(coupon.to_dict())

@coupons_bp.route('/<code>', methods=['DELETE'])
@jwt_required()
def delete_coupon(code):
    user_id = get_jwt_identity()
    user = User.get_by_id(user_id)
    
    if not user.is_admin():
        return handle_unauthorized_error('Admin access required')
        
    coupon = Coupon.get_by_code(code)
    if not coupon:
        return handle_not_found_error('Coupon not found')
        
    coupon.delete()
    return '', 204

@coupons_bp.route('/<code>/validate', methods=['POST'])
def validate_coupon(code):
    data = request.get_json()
    total_amount = data.get('total_amount')
    
    if not total_amount:
        return handle_validation_error('Total amount is required')
        
    coupon = Coupon.get_by_code(code)
    if not coupon:
        return handle_not_found_error('Coupon not found')
        
    if not coupon.is_valid(total_amount):
        return handle_validation_error('Coupon is not valid')
        
    return jsonify({
        'valid': True,
        'discount_amount': coupon.calculate_discount(total_amount)
    }) 