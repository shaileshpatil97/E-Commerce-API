# E-Commerce Backend API

A scalable and robust E-Commerce backend API built with Flask, MongoDB, Redis, and Celery. This API provides a complete solution for managing an e-commerce platform with features like product management, cart operations, order processing, user authentication, and coupon management.

## Features

- **User Authentication & Authorization**
  - JWT-based authentication
  - Role-based access control (Admin/Customer)
  - Secure password hashing
  - Refresh token mechanism

- **Product Management**
  - CRUD operations for products
  - Category-based organization
  - Stock management
  - Search and filtering capabilities

- **Cart Management**
  - Add/remove items
  - Update quantities
  - Price calculations
  - Stock validation

- **Order Processing**
  - Order creation and management
  - Status tracking
  - Real-time updates via WebSocket
  - Email notifications
  - Shipping address validation

- **Coupon System**
  - Percentage and fixed discount support
  - Usage limits and validity periods
  - Minimum purchase requirements
  - Maximum discount caps

- **Performance & Scalability**
  - Redis caching
  - Rate limiting
  - Background task processing with Celery
  - Real-time updates with WebSocket

## Tech Stack

- **Backend Framework**: Flask
- **Database**: MongoDB
- **Caching**: Redis
- **Task Queue**: Celery
- **Real-time Communication**: Flask-SocketIO
- **Authentication**: Flask-JWT-Extended
- **API Documentation**: Swagger/OpenAPI
- **Testing**: pytest
- **CI/CD**: GitHub Actions
- **Deployment**: AWS Elastic Beanstalk

## Prerequisites

- Python 3.8+
- MongoDB
- Redis
- RabbitMQ (for Celery)
- AWS Account (for deployment)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/shaileshpatil97/ecommerce-api.git
cd ecommerce-api
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

## Running the Application

1. Start Redis:
```bash
redis-server
```

2. Start Celery worker:
```bash
celery -A app.celery worker --loglevel=info
```

3. Run the Flask application:
```bash
flask run
```

## API Documentation

The API documentation is available at `/api/docs` when running the application. It provides detailed information about all available endpoints, request/response formats, and authentication requirements.

## Testing

Run the test suite:
```bash
pytest
```

Generate coverage report:
```bash
pytest --cov=app tests/
```

## Deployment

The application is configured for deployment on AWS Elastic Beanstalk. The deployment process is automated using GitHub Actions.

1. Set up AWS credentials in GitHub Secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION`

2. Configure Elastic Beanstalk environment variables in `aws/elastic-beanstalk/config.yml`

3. Push to the main branch to trigger automatic deployment

## Project Structure

```
ecommerce-api/
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── cart.py
│   │   ├── order.py
│   │   └── coupon.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── products.py
│   │   ├── cart.py
│   │   ├── orders.py
│   │   ├── coupons.py
│   │   └── admin.py
│   ├── utils/
│   │   ├── validators.py
│   │   ├── error_handlers.py
│   │   └── cache.py
│   ├── tasks.py
│   └── websocket.py
├── tests/
│   └── test_api.py
├── aws/
│   └── elastic-beanstalk/
│       └── config.yml
├── .github/
│   └── workflows/
│       └── deploy.yml
├── requirements.txt
├── config.py
└── run.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask documentation and community
- MongoDB documentation
- AWS Elastic Beanstalk documentation
- GitHub Actions documentation 
