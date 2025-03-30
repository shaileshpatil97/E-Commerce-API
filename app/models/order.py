from datetime import datetime
from app import mongo
from bson import ObjectId
from app.models.product import Product

class OrderItem:
    def __init__(self, product_id, quantity, price):
        self.product_id = product_id
        self.quantity = int(quantity)
        self.price = float(price)

    def to_dict(self):
        return {
            'product_id': self.product_id,
            'quantity': self.quantity,
            'price': self.price
        }

class Order:
    def __init__(self, user_id, items, shipping_address, total_amount):
        self.user_id = user_id
        self.items = items
        self.shipping_address = shipping_address
        self.total_amount = float(total_amount)
        self.status = 'pending'
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    @staticmethod
    def find_by_id(order_id, db):
        try:
            order_data = db.orders.find_one({'_id': ObjectId(order_id)})
            if order_data:
                order = Order(
                    user_id=order_data['user_id'],
                    items=[OrderItem(**item) for item in order_data['items']],
                    shipping_address=order_data['shipping_address'],
                    total_amount=order_data['total_amount']
                )
                order.id = str(order_data['_id'])
                order.status = order_data['status']
                order.created_at = order_data['created_at']
                order.updated_at = order_data['updated_at']
                return order
            return None
        except:
            return None

    @staticmethod
    def find_by_user_id(user_id, db, page=1, per_page=10):
        skip = (page - 1) * per_page
        orders_data = list(db.orders.find({'user_id': user_id})
                         .sort('created_at', -1)
                         .skip(skip)
                         .limit(per_page))
        
        orders = []
        for order_data in orders_data:
            order = Order(
                user_id=order_data['user_id'],
                items=[OrderItem(**item) for item in order_data['items']],
                shipping_address=order_data['shipping_address'],
                total_amount=order_data['total_amount']
            )
            order.id = str(order_data['_id'])
            order.status = order_data['status']
            order.created_at = order_data['created_at']
            order.updated_at = order_data['updated_at']
            orders.append(order)
        
        return orders

    @staticmethod
    def count_by_user_id(user_id, db):
        return db.orders.count_documents({'user_id': user_id})

    def save(self, db):
        order_data = {
            'user_id': self.user_id,
            'items': [item.to_dict() for item in self.items],
            'shipping_address': self.shipping_address,
            'total_amount': self.total_amount,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        result = db.orders.insert_one(order_data)
        self.id = str(result.inserted_id)
        return self

    def update_status(self, db, new_status):
        if new_status not in ['pending', 'processing', 'shipped', 'delivered', 'cancelled']:
            return False
        
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        result = db.orders.update_one(
            {'_id': ObjectId(self.id)},
            {
                '$set': {
                    'status': self.status,
                    'updated_at': self.updated_at
                }
            }
        )
        return result.modified_count > 0

    def cancel(self, db):
        if self.status not in ['pending', 'processing']:
            return False
        
        # Restore product stock
        for item in self.items:
            product = Product.find_by_id(item.product_id, db)
            if product:
                product.update_stock(db, item.quantity)
        
        return self.update_status(db, 'cancelled')

    def to_dict(self, db):
        items = []
        for item in self.items:
            product = Product.find_by_id(item.product_id, db)
            if product:
                items.append({
                    'product': product.to_dict(),
                    'quantity': item.quantity,
                    'price': item.price
                })

        return {
            'id': self.id,
            'user_id': self.user_id,
            'items': items,
            'shipping_address': self.shipping_address,
            'total_amount': self.total_amount,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 