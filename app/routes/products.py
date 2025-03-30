from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.product import Product
from app.models.user import User
from app.utils.validators import validate_price, validate_stock
from app.utils.error_handlers import handle_validation_error, handle_unauthorized_error, handle_not_found_error
from app import mongo, cache

products_bp = Blueprint('products', __name__)

@products_bp.route('/', methods=['GET'])
@cache.cached(timeout=300)
def get_products():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    category = request.args.get('category')
    search = request.args.get('search')
    
    # Build query
    query = {}
    if category:
        query['category'] = category
    if search:
        query['$or'] = [
            {'name': {'$regex': search, '$options': 'i'}},
            {'description': {'$regex': search, '$options': 'i'}}
        ]
    
    # Get products
    products = Product.find(query, page, per_page)
    total = Product.count(query)
    
    return jsonify({
        'products': [product.to_dict() for product in products],
        'total': total,
        'page': page,
        'per_page': per_page
    }), 200

@products_bp.route('/<product_id>', methods=['GET'])
@cache.cached(timeout=300)
def get_product(product_id):
    product = Product.get_by_id(product_id)
    if not product:
        return handle_not_found_error('Product not found')
    
    return jsonify(product.to_dict()), 200

@products_bp.route('/', methods=['POST'])
@jwt_required()
def create_product():
    # Check if user is admin
    current_user_id = get_jwt_identity()
    user = User.find_by_id(current_user_id, mongo.db)
    if not user or user.role != 'admin':
        return handle_unauthorized_error('Admin access required')
    
    data = request.get_json()
    
    # Validate required fields
    if not all(k in data for k in ['name', 'description', 'price', 'category', 'stock']):
        return handle_validation_error('Missing required fields')
    
    # Validate price and stock
    if not validate_price(data['price']):
        return handle_validation_error('Invalid price')
    if not validate_stock(data['stock']):
        return handle_validation_error('Invalid stock')
    
    # Create product
    product = Product(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        category=data['category'],
        stock=data['stock'],
        image_url=data.get('image_url')
    )
    product.save(mongo.db)
    
    # Clear cache
    cache.delete_memoized(get_products)
    
    return jsonify({
        'message': 'Product created successfully',
        'product': product.to_dict()
    }), 201

@products_bp.route('/<product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    # Check if user is admin
    current_user_id = get_jwt_identity()
    user = User.find_by_id(current_user_id, mongo.db)
    if not user or user.role != 'admin':
        return handle_unauthorized_error('Admin access required')
    
    product = Product.get_by_id(product_id)
    if not product:
        return handle_not_found_error('Product not found')
    
    data = request.get_json()
    
    # Validate price and stock if provided
    if 'price' in data and not validate_price(data['price']):
        return handle_validation_error('Invalid price')
    if 'stock' in data and not validate_stock(data['stock']):
        return handle_validation_error('Invalid stock')
    
    # Update product
    for key, value in data.items():
        setattr(product, key, value)
    product.save()
    
    # Clear cache
    cache.delete_memoized(get_products)
    cache.delete_memoized(get_product, product_id)
    
    return jsonify({
        'message': 'Product updated successfully',
        'product': product.to_dict()
    }), 200

@products_bp.route('/<product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    # Check if user is admin
    current_user_id = get_jwt_identity()
    user = User.find_by_id(current_user_id, mongo.db)
    if not user or user.role != 'admin':
        return handle_unauthorized_error('Admin access required')
    
    product = Product.get_by_id(product_id)
    if not product:
        return handle_not_found_error('Product not found')
    
    product.delete()
    
    # Clear cache
    cache.delete_memoized(get_products)
    cache.delete_memoized(get_product, product_id)
    
    return jsonify({
        'message': 'Product deleted successfully'
    }), 200

@products_bp.route('/<product_id>/stock', methods=['PUT'])
@jwt_required()
def update_stock(product_id):
    # Check if user is admin
    current_user_id = get_jwt_identity()
    user = User.find_by_id(current_user_id, mongo.db)
    if not user or user.role != 'admin':
        return handle_unauthorized_error('Admin access required')
    
    product = Product.get_by_id(product_id)
    if not product:
        return handle_not_found_error('Product not found')
    
    data = request.get_json()
    if 'quantity' not in data:
        return handle_validation_error('Missing quantity')
    
    quantity = int(data['quantity'])
    if not validate_stock(quantity):
        return handle_validation_error('Invalid quantity')
    
    if product.update_stock(mongo.db, quantity):
        return jsonify({
            'message': 'Stock updated successfully',
            'product': product.to_dict()
        }), 200
    
    return handle_validation_error('Failed to update stock') 