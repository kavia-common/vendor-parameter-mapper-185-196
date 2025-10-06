import json
import os
from app import app, api, create_app  # import your Flask app and Api instance

# Ensure app context is available
the_app = app if app else create_app()
with the_app.app_context():
    # flask-smorest stores the spec in api.spec
    from app import api as the_api
    openapi_spec = the_api.spec.to_dict()

    output_dir = "interfaces"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "openapi.json")

    with open(output_path, "w") as f:
        json.dump(openapi_spec, f, indent=2)
