from celery import Celery
from flask_mail import Message
from app import create_app, mail, mongo
from app.models.order import Order
from app.models.user import User
from app.models.coupon import Coupon
from datetime import datetime

# Initialize Celery
celery = Celery('tasks', broker='redis://localhost:6379/2')

# Configure Celery
celery.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/1',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@celery.task
def send_order_confirmation_email(user_email, order_id):
    """Send order confirmation email to user."""
    try:
        order = Order.get_by_id(order_id)
        user = User.get_by_email(user_email)
        
        if not order or not user:
            return False
            
        msg = Message(
            subject='Order Confirmation',
            recipients=[user_email]
        )
        
        msg.body = f"""
        Dear {user.name},
        
        Thank you for your order! Here are your order details:
        
        Order ID: {order.id}
        Total Amount: ${order.total_amount}
        Status: {order.status}
        
        Order Items:
        """
        
        for item in order.items:
            msg.body += f"\n- {item['product_name']}: {item['quantity']} x ${item['price']}"
            
        msg.body += f"""
        
        Shipping Address:
        {order.shipping_address['street']}
        {order.shipping_address['city']}, {order.shipping_address['state']} {order.shipping_address['zip_code']}
        {order.shipping_address['country']}
        
        We'll notify you when your order ships.
        
        Best regards,
        Your E-Commerce Team
        """
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

@celery.task
def update_order_status(order_id, new_status):
    """Update order status and send notification email."""
    try:
        order = Order.get_by_id(order_id)
        if not order:
            return False
            
        order.status = new_status
        order.save()
        
        user = User.get_by_id(order.user_id)
        if user:
            send_status_update_email.delay(user.email, order_id, new_status)
            
        return True
    except Exception as e:
        print(f"Error updating order status: {str(e)}")
        return False

@celery.task
def send_status_update_email(user_email, order_id, new_status):
    """Send order status update email to user."""
    try:
        order = Order.get_by_id(order_id)
        user = User.get_by_email(user_email)
        
        if not order or not user:
            return False
            
        msg = Message(
            subject='Order Status Update',
            recipients=[user_email]
        )
        
        msg.body = f"""
        Dear {user.name},
        
        Your order status has been updated:
        
        Order ID: {order.id}
        New Status: {new_status}
        
        You can track your order at: /orders/{order.id}
        
        Best regards,
        Your E-Commerce Team
        """
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending status update email: {str(e)}")
        return False

@celery.task
def cleanup_expired_coupons():
    """Clean up expired coupons."""
    try:
        current_date = datetime.utcnow()
        expired_coupons = Coupon.find_expired(current_date)
        
        for coupon in expired_coupons:
            coupon.is_active = False
            coupon.save()
            
        return len(expired_coupons)
    except Exception as e:
        print(f"Error cleaning up expired coupons: {str(e)}")
        return 0 