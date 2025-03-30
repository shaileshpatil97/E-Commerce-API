from datetime import datetime
from app import mongo
from bson import ObjectId
from app.models.product import Product

class CartItem:
    def __init__(self, product_id, quantity):
        self.product_id = product_id
        self.quantity = int(quantity)

    def to_dict(self):
        return {
            'product_id': self.product_id,
            'quantity': self.quantity
        }

class Cart:
    def __init__(self, user_id):
        self.user_id = user_id
        self.items = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    @staticmethod
    def find_by_user_id(user_id, db):
        cart_data = db.carts.find_one({'user_id': user_id})
        if cart_data:
            cart = Cart(user_id=cart_data['user_id'])
            cart.id = str(cart_data['_id'])
            cart.items = [CartItem(**item) for item in cart_data['items']]
            cart.created_at = cart_data['created_at']
            cart.updated_at = cart_data['updated_at']
            return cart
        return None

    def save(self, db):
        cart_data = {
            'user_id': self.user_id,
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        result = db.carts.insert_one(cart_data)
        self.id = str(result.inserted_id)
        return self

    def update(self, db):
        cart_data = {
            'items': [item.to_dict() for item in self.items],
            'updated_at': datetime.utcnow()
        }
        result = db.carts.update_one(
            {'_id': ObjectId(self.id)},
            {'$set': cart_data}
        )
        return result.modified_count > 0

    def add_item(self, db, product_id, quantity):
        # Check if product exists and has enough stock
        product = Product.find_by_id(product_id, db)
        if not product or product.stock < quantity:
            return False

        # Check if item already exists in cart
        for item in self.items:
            if item.product_id == product_id:
                new_quantity = item.quantity + quantity
                if product.stock < new_quantity:
                    return False
                item.quantity = new_quantity
                self.update(db)
                return True

        # Add new item
        self.items.append(CartItem(product_id, quantity))
        self.update(db)
        return True

    def remove_item(self, db, product_id):
        self.items = [item for item in self.items if item.product_id != product_id]
        return self.update(db)

    def update_item_quantity(self, db, product_id, quantity):
        # Check if product exists and has enough stock
        product = Product.find_by_id(product_id, db)
        if not product or product.stock < quantity:
            return False

        # Update item quantity
        for item in self.items:
            if item.product_id == product_id:
                item.quantity = quantity
                return self.update(db)
        return False

    def clear(self, db):
        self.items = []
        return self.update(db)

    def get_total(self, db):
        total = 0
        for item in self.items:
            product = Product.find_by_id(item.product_id, db)
            if product:
                total += product.price * item.quantity
        return total

    def to_dict(self, db):
        items = []
        for item in self.items:
            product = Product.find_by_id(item.product_id, db)
            if product:
                items.append({
                    'product': product.to_dict(),
                    'quantity': item.quantity
                })

        return {
            'id': self.id,
            'user_id': self.user_id,
            'items': items,
            'total': self.get_total(db),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 