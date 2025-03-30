from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.cart import Cart
from app.models.product import Product
from app.utils.validators import validate_quantity
from app.utils.error_handlers import handle_validation_error, handle_not_found_error

carts_bp = Blueprint('carts', __name__)

@carts_bp.route('/', methods=['GET'])
@jwt_required()
def get_cart():
    user_id = get_jwt_identity()
    cart = Cart.get_by_user_id(user_id)
    
    if not cart:
        cart = Cart(user_id=user_id)
        cart.save()
    
    return jsonify(cart.to_dict())

@carts_bp.route('/items', methods=['POST'])
@jwt_required()
def add_item():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate input
    if not validate_quantity(data.get('quantity')):
        return handle_validation_error('Invalid quantity')
        
    # Get product
    product = Product.get_by_id(data['product_id'])
    if not product:
        return handle_not_found_error('Product not found')
        
    # Get or create cart
    cart = Cart.get_by_user_id(user_id)
    if not cart:
        cart = Cart(user_id=user_id)
    
    # Add item to cart
    cart.add_item(product, data['quantity'])
    cart.save()
    
    return jsonify(cart.to_dict())

@carts_bp.route('/items/<product_id>', methods=['PUT'])
@jwt_required()
def update_item(product_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate input
    if not validate_quantity(data.get('quantity')):
        return handle_validation_error('Invalid quantity')
        
    # Get cart
    cart = Cart.get_by_user_id(user_id)
    if not cart:
        return handle_not_found_error('Cart not found')
        
    # Update item quantity
    if not cart.update_item_quantity(product_id, data['quantity']):
        return handle_not_found_error('Item not found in cart')
        
    cart.save()
    return jsonify(cart.to_dict())

@carts_bp.route('/items/<product_id>', methods=['DELETE'])
@jwt_required()
def remove_item(product_id):
    user_id = get_jwt_identity()
    
    # Get cart
    cart = Cart.get_by_user_id(user_id)
    if not cart:
        return handle_not_found_error('Cart not found')
        
    # Remove item
    if not cart.remove_item(product_id):
        return handle_not_found_error('Item not found in cart')
        
    cart.save()
    return jsonify(cart.to_dict())

@carts_bp.route('/', methods=['DELETE'])
@jwt_required()
def clear_cart():
    user_id = get_jwt_identity()
    
    # Get cart
    cart = Cart.get_by_user_id(user_id)
    if not cart:
        return handle_not_found_error('Cart not found')
        
    # Clear cart
    cart.clear()
    cart.save()
    
    return jsonify(cart.to_dict()) 