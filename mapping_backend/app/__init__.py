from flask import Flask
from flask_cors import CORS
from flask_smorest import Api

from .errors import register_error_handlers
from .db import teardown_mongo_client
from .routes.health import blp as health_blp
from .routes.vendors import blp as vendors_blp
from .routes.mappings import blp as mappings_blp
from .routes.history import blp as history_blp
from .routes.resolve import blp as resolve_blp

app = Flask(__name__)
app.url_map.strict_slashes = False
CORS(app, resources={r"/*": {"origins": "*"}})

# OpenAPI / Swagger config
app.config["API_TITLE"] = "Vendor Parameter Mapping API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config["OPENAPI_URL_PREFIX"] = "/docs"
app.config["OPENAPI_SWAGGER_UI_PATH"] = ""
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

# Register error handling and db teardown
register_error_handlers(app)
app.teardown_appcontext(teardown_mongo_client)

api = Api(app)
api.register_blueprint(health_blp)
api.register_blueprint(vendors_blp)
api.register_blueprint(mappings_blp)
api.register_blueprint(history_blp)
api.register_blueprint(resolve_blp)
