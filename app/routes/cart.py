from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.cart import Cart
from app.models.product import Product
from app.models.coupon import Coupon
from app.utils.validators import validate_quantity
from app.utils.error_handlers import handle_validation_error, handle_not_found_error
from app import mongo

cart_bp = Blueprint('cart', __name__)

@cart_bp.route('', methods=['GET'])
@jwt_required()
def get_cart():
    current_user_id = get_jwt_identity()
    cart = Cart.find_by_user_id(current_user_id, mongo.db)
    
    if not cart:
        cart = Cart(current_user_id)
        cart.save(mongo.db)
    
    return jsonify({
        'cart': cart.to_dict(mongo.db)
    }), 200

@cart_bp.route('/items', methods=['POST'])
@jwt_required()
def add_to_cart():
    current_user_id = get_jwt_identity()
    cart = Cart.find_by_user_id(current_user_id, mongo.db)
    
    if not cart:
        cart = Cart(current_user_id)
        cart.save(mongo.db)
    
    data = request.get_json()
    
    # Validate required fields
    if not all(k in data for k in ['product_id', 'quantity']):
        return handle_validation_error('Missing required fields')
    
    # Validate quantity
    if not validate_quantity(data['quantity']):
        return handle_validation_error('Invalid quantity')
    
    # Add item to cart
    if cart.add_item(mongo.db, data['product_id'], data['quantity']):
        return jsonify({
            'message': 'Item added to cart successfully',
            'cart': cart.to_dict(mongo.db)
        }), 200
    
    return handle_validation_error('Failed to add item to cart')

@cart_bp.route('/items/<product_id>', methods=['DELETE'])
@jwt_required()
def remove_from_cart(product_id):
    current_user_id = get_jwt_identity()
    cart = Cart.find_by_user_id(current_user_id, mongo.db)
    
    if not cart:
        return handle_not_found_error('Cart not found')
    
    if cart.remove_item(mongo.db, product_id):
        return jsonify({
            'message': 'Item removed from cart successfully',
            'cart': cart.to_dict(mongo.db)
        }), 200
    
    return handle_validation_error('Failed to remove item from cart')

@cart_bp.route('/items/<product_id>', methods=['PUT'])
@jwt_required()
def update_cart_item(product_id):
    current_user_id = get_jwt_identity()
    cart = Cart.find_by_user_id(current_user_id, mongo.db)
    
    if not cart:
        return handle_not_found_error('Cart not found')
    
    data = request.get_json()
    if 'quantity' not in data:
        return handle_validation_error('Missing quantity')
    
    # Validate quantity
    if not validate_quantity(data['quantity']):
        return handle_validation_error('Invalid quantity')
    
    if cart.update_item_quantity(mongo.db, product_id, data['quantity']):
        return jsonify({
            'message': 'Cart item updated successfully',
            'cart': cart.to_dict(mongo.db)
        }), 200
    
    return handle_validation_error('Failed to update cart item')

@cart_bp.route('/items', methods=['DELETE'])
@jwt_required()
def clear_cart():
    current_user_id = get_jwt_identity()
    cart = Cart.find_by_user_id(current_user_id, mongo.db)
    
    if not cart:
        return handle_not_found_error('Cart not found')
    
    if cart.clear(mongo.db):
        return jsonify({
            'message': 'Cart cleared successfully',
            'cart': cart.to_dict(mongo.db)
        }), 200
    
    return handle_validation_error('Failed to clear cart')

@cart_bp.route('/coupon', methods=['POST'])
@jwt_required()
def apply_coupon():
    current_user_id = get_jwt_identity()
    cart = Cart.find_by_user_id(current_user_id, mongo.db)
    
    if not cart:
        return handle_not_found_error('Cart not found')
    
    data = request.get_json()
    if 'code' not in data:
        return handle_validation_error('Missing coupon code')
    
    coupon = Coupon.find_by_code(data['code'], mongo.db)
    if not coupon:
        return handle_not_found_error('Coupon not found')
    
    # Validate coupon
    is_valid, error_message = coupon.validate(cart.get_total(mongo.db))
    if not is_valid:
        return handle_validation_error(error_message)
    
    # Calculate discount
    discount = coupon.calculate_discount(cart.get_total(mongo.db))
    
    return jsonify({
        'message': 'Coupon applied successfully',
        'discount': discount,
        'cart': cart.to_dict(mongo.db)
    }), 200 