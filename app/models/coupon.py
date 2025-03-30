from datetime import datetime
from app import mongo
from bson import ObjectId

class Coupon:
    def __init__(self, code, discount_type, discount_value, min_purchase=0, 
                 max_discount=None, start_date=None, end_date=None, usage_limit=None):
        self.code = code.upper()
        self.discount_type = discount_type  # 'percentage' or 'fixed'
        self.discount_value = float(discount_value)
        self.min_purchase = float(min_purchase)
        self.max_discount = float(max_discount) if max_discount else None
        self.start_date = start_date or datetime.utcnow()
        self.end_date = end_date
        self.usage_limit = int(usage_limit) if usage_limit else None
        self.usage_count = 0
        self.is_active = True
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    @staticmethod
    def find_by_code(code, db):
        coupon_data = db.coupons.find_one({'code': code.upper()})
        if coupon_data:
            coupon = Coupon(
                code=coupon_data['code'],
                discount_type=coupon_data['discount_type'],
                discount_value=coupon_data['discount_value'],
                min_purchase=coupon_data['min_purchase'],
                max_discount=coupon_data.get('max_discount'),
                start_date=coupon_data['start_date'],
                end_date=coupon_data.get('end_date'),
                usage_limit=coupon_data.get('usage_limit')
            )
            coupon.id = str(coupon_data['_id'])
            coupon.usage_count = coupon_data['usage_count']
            coupon.is_active = coupon_data['is_active']
            coupon.created_at = coupon_data['created_at']
            coupon.updated_at = coupon_data['updated_at']
            return coupon
        return None

    @staticmethod
    def find_all(db, page=1, per_page=10):
        skip = (page - 1) * per_page
        coupons_data = list(db.coupons.find()
                          .sort('created_at', -1)
                          .skip(skip)
                          .limit(per_page))
        
        coupons = []
        for coupon_data in coupons_data:
            coupon = Coupon(
                code=coupon_data['code'],
                discount_type=coupon_data['discount_type'],
                discount_value=coupon_data['discount_value'],
                min_purchase=coupon_data['min_purchase'],
                max_discount=coupon_data.get('max_discount'),
                start_date=coupon_data['start_date'],
                end_date=coupon_data.get('end_date'),
                usage_limit=coupon_data.get('usage_limit')
            )
            coupon.id = str(coupon_data['_id'])
            coupon.usage_count = coupon_data['usage_count']
            coupon.is_active = coupon_data['is_active']
            coupon.created_at = coupon_data['created_at']
            coupon.updated_at = coupon_data['updated_at']
            coupons.append(coupon)
        
        return coupons

    @staticmethod
    def count(db):
        return db.coupons.count_documents({})

    def save(self, db):
        coupon_data = {
            'code': self.code,
            'discount_type': self.discount_type,
            'discount_value': self.discount_value,
            'min_purchase': self.min_purchase,
            'max_discount': self.max_discount,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'usage_limit': self.usage_limit,
            'usage_count': self.usage_count,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        result = db.coupons.insert_one(coupon_data)
        self.id = str(result.inserted_id)
        return self

    def update(self, db, **kwargs):
        update_data = {}
        for key, value in kwargs.items():
            if hasattr(self, key):
                if key in ['discount_value', 'min_purchase', 'max_discount']:
                    value = float(value)
                elif key in ['usage_limit', 'usage_count']:
                    value = int(value)
                elif key in ['start_date', 'end_date']:
                    value = value if isinstance(value, datetime) else datetime.fromisoformat(value)
                update_data[key] = value
        
        if update_data:
            update_data['updated_at'] = datetime.utcnow()
            result = db.coupons.update_one(
                {'_id': ObjectId(self.id)},
                {'$set': update_data}
            )
            for key, value in update_data.items():
                setattr(self, key, value)
            return result.modified_count > 0
        return False

    def delete(self, db):
        result = db.coupons.delete_one({'_id': ObjectId(self.id)})
        return result.deleted_count > 0

    def validate(self, total_amount):
        if not self.is_active:
            return False, "Coupon is not active"
        
        if self.end_date and datetime.utcnow() > self.end_date:
            return False, "Coupon has expired"
        
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False, "Coupon usage limit reached"
        
        if total_amount < self.min_purchase:
            return False, f"Minimum purchase amount of {self.min_purchase} required"
        
        return True, None

    def calculate_discount(self, total_amount):
        if self.discount_type == 'percentage':
            discount = total_amount * (self.discount_value / 100)
            if self.max_discount:
                discount = min(discount, self.max_discount)
            return discount
        else:
            return self.discount_value

    def increment_usage(self, db):
        self.usage_count += 1
        return self.update(db, usage_count=self.usage_count)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'discount_type': self.discount_type,
            'discount_value': self.discount_value,
            'min_purchase': self.min_purchase,
            'max_discount': self.max_discount,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'usage_limit': self.usage_limit,
            'usage_count': self.usage_count,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 