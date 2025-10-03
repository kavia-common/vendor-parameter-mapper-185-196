from flask import jsonify
from werkzeug.exceptions import HTTPException


class APIError(HTTPException):
    """Base API error for structured JSON error responses."""

    code = 400
    description = "Bad Request"

    def __init__(self, message=None, code=None, errors=None):
        super().__init__(description=message or self.description)
        if code is not None:
            self.code = code
        self.errors = errors or {}

    def to_response(self):
        payload = {
            "code": self.code,
            "status": self.__class__.__name__,
            "message": self.description,
            "errors": self.errors,
        }
        response = jsonify(payload)
        response.status_code = self.code
        return response


class NotFoundError(APIError):
    code = 404
    description = "Resource not found"


class ConflictError(APIError):
    code = 409
    description = "Conflict"


class ValidationError(APIError):
    code = 422
    description = "Validation error"


def register_error_handlers(app):
    """Register JSON error handlers on the Flask app."""
    @app.errorhandler(APIError)
    def handle_api_error(err: APIError):
        return err.to_response()

    @app.errorhandler(HTTPException)
    def handle_http_exception(err: HTTPException):
        payload = {
            "code": err.code or 500,
            "status": err.name or "HTTPException",
            "message": err.description or "Internal Server Error",
            "errors": {},
        }
        response = jsonify(payload)
        response.status_code = err.code or 500
        return response

    @app.errorhandler(Exception)
    def handle_uncaught_exception(err: Exception):
        payload = {
            "code": 500,
            "status": "InternalServerError",
            "message": "An unexpected error occurred",
            "errors": {},
        }
        response = jsonify(payload)
        response.status_code = 500
        return response
