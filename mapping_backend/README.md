# Mapping Backend - Vendor Parameter Mapper

This Flask service provides REST APIs for managing vendors, parameters, mappings, bulk uploads, mapping resolution, and history tracking.

Tech stack:
- Flask 3, flask-smorest (OpenAPI), flask-cors
- PyMongo for MongoDB
- Marshmallow for request/response schemas
- python-dotenv for configuration

Environment
- Copy .env.example to .env and set variables as needed.

Run locally
1. python -m venv .venv && source .venv/bin/activate
2. pip install -r requirements.txt
3. cp .env.example .env
4. Ensure MongoDB is running and MONGO_URI points to it.
5. python run.py
6. Optional: seed sample data: python scripts/seed.py
7. Open API docs at /docs

Environment variables
- FLASK_ENV, FLASK_DEBUG, PORT
- MONGO_URI, MONGO_DB_NAME
- CORS_ORIGINS

API base path
- All endpoints are prefixed with /api

Health
- GET /api/ (health check)

Vendors
- GET /api/vendors?page=&pageSize=
- POST /api/vendors
- GET /api/vendors/<id>
- PATCH /api/vendors/<id>
- DELETE /api/vendors/<id>

Parameters
- GET /api/parameters?page=&pageSize=
- POST /api/parameters/bulk (JSON: { items: [ { key, description?, dataType?, allowedValues? } ] })

Mappings
- GET /api/mappings?vendorId=&namespace=&page=&pageSize=
- POST /api/mappings
- POST /api/mappings/bulk (JSON or CSV)
  - CSV headers: vendor_id,namespace,input_param,output_param,transform
- GET /api/mappings/<id>
- PATCH /api/mappings/<id>
- DELETE /api/mappings/<id>

Resolve
- POST /api/resolve
  Request:
  {
    "vendor_id": "ObjectId",
    "namespace": "default",
    "parameters": ["first_name","last_name","age"],
    "values": {"first_name":"Jane","last_name":"Doe","age":"34"}
  }
  Response: { vendor_id, namespace, resolved: { fname: "JANE", lname: "Doe", age_years: 34 }, rules_used: [...] }

History
- GET /api/history?mapping_id=&vendor_id=

Notes
- JSON error format is consistent with code, 4xx/5xx handled.
- CORS is permissive by default for preview; restrict in production.
- Linting: flake8 is configured via setup.cfg/.flake8 with max-line-length 120.
