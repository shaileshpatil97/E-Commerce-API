from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import mongo
from bson import ObjectId

class User:
    def __init__(self, email, password, name, role='customer'):
        self.email = email
        self.password = generate_password_hash(password)
        self.name = name
        self.role = role
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    @staticmethod
    def from_dict(data):
        user = User(
            email=data['email'],
            password='',  # Password will be set separately
            name=data['name'],
            role=data.get('role', 'customer')
        )
        user.password = data['password']
        user.created_at = data['created_at']
        user.updated_at = data['updated_at']
        if '_id' in data:
            user.id = str(data['_id'])
        return user
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    @staticmethod
    def find_by_email(email, db):
        user_data = db.users.find_one({'email': email})
        if user_data:
            user = User(
                email=user_data['email'],
                password=user_data['password'],
                name=user_data['name'],
                role=user_data['role']
            )
            user.id = str(user_data['_id'])
            user.created_at = user_data['created_at']
            user.updated_at = user_data['updated_at']
            return user
        return None
    
    @staticmethod
    def find_by_id(user_id, db):
        try:
            user_data = db.users.find_one({'_id': ObjectId(user_id)})
            if user_data:
                user = User(
                    email=user_data['email'],
                    password=user_data['password'],
                    name=user_data['name'],
                    role=user_data['role']
                )
                user.id = str(user_data['_id'])
                user.created_at = user_data['created_at']
                user.updated_at = user_data['updated_at']
                return user
            return None
        except:
            return None
    
    def save(self, db):
        user_data = {
            'email': self.email,
            'password': self.password,
            'name': self.name,
            'role': self.role,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        result = db.users.insert_one(user_data)
        self.id = str(result.inserted_id)
        return self
    
    def update(self, db, **kwargs):
        update_data = {}
        for key, value in kwargs.items():
            if hasattr(self, key):
                if key == 'password':
                    value = generate_password_hash(value)
                update_data[key] = value
        
        if update_data:
            update_data['updated_at'] = datetime.utcnow()
            db.users.update_one(
                {'_id': ObjectId(self.id)},
                {'$set': update_data}
            )
            for key, value in update_data.items():
                setattr(self, key, value)
            return True
        return False
    
    def delete(self, db):
        result = db.users.delete_one({'_id': ObjectId(self.id)})
        return result.deleted_count > 0
    
    def is_admin(self):
        return self.role == 'admin' 