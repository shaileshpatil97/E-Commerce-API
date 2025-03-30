from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_jwt_extended import decode_token
from functools import wraps
from app.models.order import Order
from app.models.user import User
from app import mongo

socketio = SocketIO()

def authenticated_only(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        token = kwargs.get('token')
        if not token:
            emit('error', {'message': 'Missing token'})
            return
        
        try:
            decoded_token = decode_token(token)
            user_id = decoded_token['sub']
            user = User.find_by_id(user_id, mongo.db)
            if not user:
                emit('error', {'message': 'Invalid user'})
                return
            return f(*args, **kwargs)
        except Exception as e:
            emit('error', {'message': 'Invalid token'})
    return wrapped

@socketio.on('connect')
@authenticated_only
def handle_connect(token):
    try:
        decoded_token = decode_token(token)
        user_id = decoded_token['sub']
        user = User.find_by_id(user_id, mongo.db)
        
        # Join user's personal room
        join_room(f'user_{user_id}')
        
        # If user is admin, join admin room
        if user.role == 'admin':
            join_room('admin')
        
        emit('connected', {'message': 'Connected successfully'})
    except Exception as e:
        emit('error', {'message': 'Connection failed'})

@socketio.on('disconnect')
def handle_disconnect():
    emit('disconnected', {'message': 'Disconnected successfully'})

@socketio.on('join_order')
@authenticated_only
def handle_join_order(order_id, token):
    try:
        decoded_token = decode_token(token)
        user_id = decoded_token['sub']
        user = User.find_by_id(user_id, mongo.db)
        
        # Check if order exists
        order = Order.find_by_id(order_id, mongo.db)
        if not order:
            emit('error', {'message': 'Order not found'})
            return
        
        # Check if user is authorized to view the order
        if user.role != 'admin' and order.user_id != user_id:
            emit('error', {'message': 'Unauthorized access'})
            return
        
        # Join order room
        join_room(f'order_{order_id}')
        emit('joined_order', {'message': f'Joined order room: {order_id}'})
    except Exception as e:
        emit('error', {'message': 'Failed to join order room'})

@socketio.on('leave_order')
def handle_leave_order(order_id):
    leave_room(f'order_{order_id}')
    emit('left_order', {'message': f'Left order room: {order_id}'})

def broadcast_order_update(order_id, status):
    """Broadcast order status update to all users in the order's room."""
    socketio.emit('order_status_update', {
        'order_id': order_id,
        'status': status
    }, room=f'order_{order_id}')

def broadcast_new_order(order_data):
    """Broadcast new order notification to admin room."""
    socketio.emit('new_order', order_data, room='admin')

def broadcast_order_cancellation(order_id):
    """Broadcast order cancellation to all users in the order's room."""
    socketio.emit('order_cancelled', {
        'order_id': order_id
    }, room=f'order_{order_id}') 