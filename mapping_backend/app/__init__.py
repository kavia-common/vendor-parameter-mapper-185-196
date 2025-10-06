from flask import Flask
from flask_cors import CORS
from flask_smorest import Api
from dotenv import load_dotenv
import os

from .errors import register_error_handlers
from .db import teardown_mongo_client
from .routes.health import blp as health_blp
from .routes.vendors import blp as vendors_blp
from .routes.mappings import blp as mappings_blp
from .routes.history import blp as history_blp
from .routes.resolve import blp as resolve_blp
from .routes.parameters import blp as parameters_blp

# Expose app and api for OpenAPI generation while supporting app factory
def _configure_app(app: Flask) -> Api:
    app.url_map.strict_slashes = False
    CORS(app, resources={r"/*": {"origins": os.getenv("CORS_ORIGINS", "*")}})
    # OpenAPI / Swagger config
    app.config["API_TITLE"] = "Vendor Parameter Mapping API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/docs"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = ""
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    register_error_handlers(app)
    app.teardown_appcontext(teardown_mongo_client)

    api = Api(app)
    # Register blueprints under /api
    api.register_blueprint(health_blp, url_prefix="/api")
    api.register_blueprint(vendors_blp, url_prefix="/api")
    api.register_blueprint(mappings_blp, url_prefix="/api")
    api.register_blueprint(history_blp, url_prefix="/api")
    api.register_blueprint(resolve_blp, url_prefix="/api")
    api.register_blueprint(parameters_blp, url_prefix="/api")
    return api

# PUBLIC_INTERFACE
def create_app() -> Flask:
    """Create and configure the Flask application."""
    load_dotenv()
    app = Flask(__name__)
    _configure_app(app)
    return app

# Keep compatibility for scripts that import app/api directly
load_dotenv()
app = Flask(__name__)
api = _configure_app(app)
