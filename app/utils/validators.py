import re
from datetime import datetime

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password(password):
    # Password must be at least 8 characters long and contain at least one number
    return len(password) >= 8 and any(char.isdigit() for char in password)

def validate_price(price):
    try:
        price = float(price)
        return price >= 0
    except (ValueError, TypeError):
        return False

def validate_stock(stock):
    try:
        stock = int(stock)
        return stock >= 0
    except (ValueError, TypeError):
        return False

def validate_quantity(quantity):
    try:
        quantity = int(quantity)
        return quantity > 0
    except (ValueError, TypeError):
        return False

def validate_shipping_address(address):
    required_fields = ['street', 'city', 'state', 'country', 'zip_code']
    return all(field in address for field in required_fields)

def validate_discount_value(value, discount_type):
    try:
        value = float(value)
        if discount_type == 'percentage':
            return 0 <= value <= 100
        else:  # fixed
            return value >= 0
    except (ValueError, TypeError):
        return False

def validate_dates(start_date, end_date):
    try:
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = None
        
        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = None
        
        if start and end:
            return start <= end
        return True
    except (ValueError, TypeError):
        return False 