from flask import Flask, redirect, send_from_directory
from flask_cors import CORS
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_socketio import SocketIO
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_swagger_ui import get_swaggerui_blueprint
from celery import Celery
from config import Config

# Initialize extensions
mongo = PyMongo()
jwt = JWTManager()
mail = Mail()
socketio = SocketIO()
cache = Cache()
limiter = Limiter(key_func=get_remote_address)
celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='static')
    app.config.from_object(config_class)

    # Initialize CORS
    CORS(app)

    # Add root route
    @app.route('/')
    def index():
        return redirect('/api/docs')

    # Serve swagger.json
    @app.route('/static/swagger.json')
    def serve_swagger():
        return send_from_directory(app.static_folder, 'swagger.json')

    # Initialize extensions with app
    mongo.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    socketio.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    celery.conf.update(app.config)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.products import products_bp
    from app.routes.carts import carts_bp
    from app.routes.orders import orders_bp
    from app.routes.coupons import coupons_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(carts_bp, url_prefix='/api/carts')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    app.register_blueprint(coupons_bp, url_prefix='/api/coupons')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    # Configure Swagger UI
    SWAGGER_URL = '/api/docs'
    API_URL = '/static/swagger.json'
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "E-Commerce API"
        }
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    return app 