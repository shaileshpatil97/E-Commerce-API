from flask import jsonify
from werkzeug.exceptions import HTTPException

def handle_validation_error(message, status_code=400):
    return jsonify({
        'error': 'Validation Error',
        'message': message
    }), status_code

def handle_not_found_error(message='Resource not found'):
    return jsonify({
        'error': 'Not Found',
        'message': message
    }), 404

def handle_unauthorized_error(message='Unauthorized access'):
    return jsonify({
        'error': 'Unauthorized',
        'message': message
    }), 401

def handle_forbidden_error(message='Access forbidden'):
    return jsonify({
        'error': 'Forbidden',
        'message': message
    }), 403

def handle_internal_error(message='Internal server error'):
    return jsonify({
        'error': 'Internal Server Error',
        'message': message
    }), 500

def register_error_handlers(app):
    @app.errorhandler(400)
    def handle_bad_request(error):
        return handle_validation_error(str(error))

    @app.errorhandler(401)
    def handle_unauthorized(error):
        return handle_unauthorized_error(str(error))

    @app.errorhandler(403)
    def handle_forbidden(error):
        return handle_forbidden_error(str(error))

    @app.errorhandler(404)
    def handle_not_found(error):
        return handle_not_found_error(str(error))

    @app.errorhandler(500)
    def handle_internal(error):
        return handle_internal_error(str(error))

    @app.errorhandler(Exception)
    def handle_generic_error(error):
        if isinstance(error, HTTPException):
            return jsonify({
                'error': error.name,
                'message': error.description
            }), error.code
        return handle_internal_error(str(error)) 