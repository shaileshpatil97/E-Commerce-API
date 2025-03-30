from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.order import Order
from app.models.product import Product
from app.utils.error_handlers import handle_validation_error, handle_unauthorized_error, handle_not_found_error
from app import mongo
from app.tasks import update_order_status, cleanup_expired_coupons

admin_bp = Blueprint('admin', __name__)

def admin_required():
    user_id = get_jwt_identity()
    user = User.get_by_id(user_id)
    
    if not user or not user.is_admin():
        return handle_unauthorized_error('Admin access required')
    return None

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    # Check admin access
    error = admin_required()
    if error:
        return error
    
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    # Get users with pagination
    skip = (page - 1) * per_page
    cursor = mongo.db.users.find().skip(skip).limit(per_page)
    users = [User.from_dict(user) for user in cursor]
    
    # Get total count
    total = mongo.db.users.count_documents({})
    
    return jsonify({
        'users': [user.to_dict() for user in users],
        'total': total,
        'page': page,
        'per_page': per_page
    }), 200

@admin_bp.route('/users/<user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    # Check admin access
    error = admin_required()
    if error:
        return error
    
    user = User.find_by_id(mongo.db, user_id)
    if not user:
        return handle_validation_error('User not found')
    
    return jsonify({
        'user': user.to_dict()
    }), 200

@admin_bp.route('/users/<user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    # Check admin access
    error = admin_required()
    if error:
        return error
    
    user = User.find_by_id(mongo.db, user_id)
    if not user:
        return handle_validation_error('User not found')
    
    data = request.get_json()
    
    # Update user fields
    if 'name' in data:
        user.name = data['name']
    
    if 'email' in data:
        user.email = data['email']
    
    if 'role' in data:
        if data['role'] not in ['customer', 'admin']:
            return handle_validation_error('Invalid role')
        user.role = data['role']
    
    if 'is_active' in data:
        user.is_active = data['is_active']
    
    user.save(mongo.db)
    
    return jsonify({
        'message': 'User updated successfully',
        'user': user.to_dict()
    }), 200

@admin_bp.route('/users/<user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    # Check admin access
    error = admin_required()
    if error:
        return error
    
    user = User.find_by_id(request.db, user_id)
    if not user:
        return handle_validation_error('User not found')
    
    # Prevent deleting the last admin
    if user.role == 'admin':
        admin_count = request.db.users.count_documents({'role': 'admin'})
        if admin_count <= 1:
            return handle_validation_error('Cannot delete the last admin user')
    
    # Delete user's cart and orders
    request.db.carts.delete_many({'user_id': user_id})
    request.db.orders.delete_many({'user_id': user_id})
    
    # Delete user
    request.db.users.delete_one({'_id': user.id})
    
    return jsonify({
        'message': 'User deleted successfully'
    }), 200

@admin_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_all_orders():
    error = admin_required()
    if error:
        return error
        
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    status = request.args.get('status')
    
    query = {}
    if status:
        query['status'] = status
        
    orders = Order.find(query, page, per_page)
    total = Order.count(query)
    
    return jsonify({
        'orders': [order.to_dict() for order in orders],
        'total': total,
        'page': page,
        'per_page': per_page
    })

@admin_bp.route('/orders/<order_id>', methods=['PUT'])
@jwt_required()
def update_order_status(order_id):
    error = admin_required()
    if error:
        return error
        
    order = Order.get_by_id(order_id)
    if not order:
        return handle_not_found_error('Order not found')
        
    data = request.get_json()
    new_status = data.get('status')
    
    if not new_status or new_status not in Order.STATUS_CHOICES:
        return handle_validation_error('Invalid status')
        
    order.status = new_status
    order.save()
    
    return jsonify(order.to_dict())

@admin_bp.route('/products/stats', methods=['GET'])
@jwt_required()
def get_product_stats():
    error = admin_required()
    if error:
        return error
        
    total_products = Product.count_all()
    category_stats = Product.get_category_stats()
    low_stock_products = Product.find_low_stock()
    
    return jsonify({
        'total_products': total_products,
        'category_stats': category_stats,
        'low_stock_products': [product.to_dict() for product in low_stock_products]
    })

@admin_bp.route('/orders/stats', methods=['GET'])
@jwt_required()
def get_order_stats():
    error = admin_required()
    if error:
        return error
        
    total_orders = Order.count_all()
    status_stats = Order.get_status_stats()
    total_revenue = Order.get_total_revenue()
    
    return jsonify({
        'total_orders': total_orders,
        'status_stats': status_stats,
        'total_revenue': total_revenue
    })

@admin_bp.route('/system/cleanup', methods=['POST'])
@jwt_required()
def cleanup_system():
    error = admin_required()
    if error:
        return error
        
    # Clean up expired coupons
    cleanup_expired_coupons.delay()
    
    return jsonify({
        'message': 'System cleanup initiated'
    })

@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    # Check admin access
    error = admin_required()
    if error:
        return error
    
    # Get statistics
    total_users = request.db.users.count_documents({})
    total_orders = request.db.orders.count_documents({})
    total_products = request.db.products.count_documents({})
    
    # Get recent orders
    recent_orders = list(request.db.orders.find().sort('created_at', -1).limit(5))
    recent_orders = [Order.from_dict(order).to_dict() for order in recent_orders]
    
    # Get order status counts
    status_counts = {}
    for status in ['pending', 'processing', 'shipped', 'delivered', 'cancelled']:
        count = request.db.orders.count_documents({'status': status})
        status_counts[status] = count
    
    # Get top products
    top_products = list(request.db.products.find().sort('stock', -1).limit(5))
    top_products = [Product.from_dict(product).to_dict() for product in top_products]
    
    return jsonify({
        'statistics': {
            'total_users': total_users,
            'total_orders': total_orders,
            'total_products': total_products
        },
        'recent_orders': recent_orders,
        'status_counts': status_counts,
        'top_products': top_products
    }), 200 