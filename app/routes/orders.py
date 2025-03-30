from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.order import Order
from app.models.cart import Cart
from app.models.product import Product
from app.models.coupon import Coupon
from app.models.user import User
from app.utils.error_handlers import handle_validation_error, handle_not_found_error
from app.utils.validators import validate_shipping_address
from app.tasks import send_order_confirmation_email

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/', methods=['GET'])
@jwt_required()
def get_orders():
    user_id = get_jwt_identity()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    orders = Order.find_by_user_id(user_id, page, per_page)
    total = Order.count_by_user_id(user_id)
    
    return jsonify({
        'orders': [order.to_dict() for order in orders],
        'total': total,
        'page': page,
        'per_page': per_page
    })

@orders_bp.route('/<order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    user_id = get_jwt_identity()
    order = Order.get_by_id(order_id)
    
    if not order:
        return handle_not_found_error('Order not found')
    if order.user_id != user_id:
        return handle_not_found_error('Order not found')
        
    return jsonify(order.to_dict())

@orders_bp.route('/', methods=['POST'])
@jwt_required()
def create_order():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate shipping address
    if not validate_shipping_address(data.get('shipping_address')):
        return handle_validation_error('Invalid shipping address')
        
    # Get cart
    cart = Cart.get_by_user_id(user_id)
    if not cart or not cart.items:
        return handle_validation_error('Cart is empty')
        
    # Apply coupon if provided
    coupon = None
    if data.get('coupon_code'):
        coupon = Coupon.get_by_code(data['coupon_code'])
        if not coupon or not coupon.is_valid(cart.total_amount):
            return handle_validation_error('Invalid or expired coupon')
    
    # Create order
    order = Order(
        user_id=user_id,
        items=cart.items,
        total_amount=cart.total_amount,
        shipping_address=data['shipping_address'],
        coupon=coupon
    )
    order.save()
    
    # Clear cart
    cart.clear()
    cart.save()
    
    # Send confirmation email
    send_order_confirmation_email.delay(user_id, order.id)
    
    return jsonify(order.to_dict()), 201

@orders_bp.route('/<order_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_order(order_id):
    user_id = get_jwt_identity()
    order = Order.get_by_id(order_id)
    
    if not order:
        return handle_not_found_error('Order not found')
    if order.user_id != user_id:
        return handle_not_found_error('Order not found')
    if not order.can_cancel():
        return handle_validation_error('Order cannot be cancelled')
        
    order.cancel()
    order.save()
    
    return jsonify(order.to_dict())

@orders_bp.route('/<order_id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(order_id):
    current_user_id = get_jwt_identity()
    user = User.find_by_id(request.db, current_user_id)
    
    if not user.is_admin():
        return handle_validation_error('Unauthorized'), 403
    
    data = request.get_json()
    if not data or not data.get('status'):
        return handle_validation_error('Missing status')
    
    order = Order.find_by_id(request.db, order_id)
    if not order:
        return handle_validation_error('Order not found')
    
    if order.update_status(request.db, data['status']):
        return jsonify({
            'message': 'Order status updated successfully',
            'order': order.to_dict()
        }), 200
    
    return handle_validation_error('Invalid status') 