from datetime import datetime
from app import mongo
from bson import ObjectId

class Product:
    def __init__(self, name, description, price, category, stock, image_url=None):
        self.name = name
        self.description = description
        self.price = float(price)
        self.category = category
        self.stock = int(stock)
        self.image_url = image_url
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    @staticmethod
    def from_dict(data):
        product = Product(
            name=data['name'],
            description=data['description'],
            price=data['price'],
            category=data['category'],
            stock=data['stock'],
            image_url=data.get('image_url')
        )
        product.created_at = data['created_at']
        product.updated_at = data['updated_at']
        if '_id' in data:
            product.id = str(data['_id'])
        return product
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'category': self.category,
            'stock': self.stock,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @staticmethod
    def find_by_id(product_id, db):
        try:
            product_data = db.products.find_one({'_id': ObjectId(product_id)})
            if product_data:
                product = Product(
                    name=product_data['name'],
                    description=product_data['description'],
                    price=product_data['price'],
                    category=product_data['category'],
                    stock=product_data['stock'],
                    image_url=product_data.get('image_url')
                )
                product.id = str(product_data['_id'])
                product.created_at = product_data['created_at']
                product.updated_at = product_data['updated_at']
                return product
            return None
        except:
            return None
    
    @staticmethod
    def find_by_category(db, category, page=1, per_page=10):
        skip = (page - 1) * per_page
        cursor = db.products.find({'category': category}).skip(skip).limit(per_page)
        return [Product.from_dict(product) for product in cursor]
    
    @staticmethod
    def find_all(db, category=None, page=1, per_page=10):
        query = {}
        if category:
            query['category'] = category
        
        skip = (page - 1) * per_page
        products_data = list(db.products.find(query).skip(skip).limit(per_page))
        
        products = []
        for product_data in products_data:
            product = Product(
                name=product_data['name'],
                description=product_data['description'],
                price=product_data['price'],
                category=product_data['category'],
                stock=product_data['stock'],
                image_url=product_data.get('image_url')
            )
            product.id = str(product_data['_id'])
            product.created_at = product_data['created_at']
            product.updated_at = product_data['updated_at']
            products.append(product)
        
        return products
    
    @staticmethod
    def count(db, category=None):
        query = {}
        if category:
            query['category'] = category
        return db.products.count_documents(query)
    
    def save(self, db):
        product_data = {
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'category': self.category,
            'stock': self.stock,
            'image_url': self.image_url,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        result = db.products.insert_one(product_data)
        self.id = str(result.inserted_id)
        return self
    
    def update(self, db, **kwargs):
        update_data = {}
        for key, value in kwargs.items():
            if hasattr(self, key):
                if key in ['price', 'stock']:
                    value = float(value) if key == 'price' else int(value)
                update_data[key] = value
        
        if update_data:
            update_data['updated_at'] = datetime.utcnow()
            db.products.update_one(
                {'_id': ObjectId(self.id)},
                {'$set': update_data}
            )
            for key, value in update_data.items():
                setattr(self, key, value)
            return True
        return False
    
    def delete(self, db):
        result = db.products.delete_one({'_id': ObjectId(self.id)})
        return result.deleted_count > 0
    
    def update_stock(self, db, quantity):
        if self.stock + quantity >= 0:
            self.stock += quantity
            self.update(db, stock=self.stock)
            return True
        return False 