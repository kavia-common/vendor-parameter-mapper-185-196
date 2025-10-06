from flask_smorest import Blueprint
from flask.views import MethodView
from flask import request
from marshmallow import Schema, fields, validate

from ..db import get_db
from ..errors import ValidationError

blp = Blueprint("Parameters", "parameters", url_prefix="/parameters", description="Parameters catalog")

class ParameterSchema(Schema):
    id = fields.Str(required=True, description="Parameter ID")
    key = fields.Str(required=True, description="Unique parameter key")
    description = fields.Str(allow_none=True)
    dataType = fields.Str(allow_none=True)
    allowedValues = fields.List(fields.Raw(), required=False)

def _doc_to_dict(doc):
    return {
        "id": str(doc["_id"]),
        "key": doc["key"],
        "description": doc.get("description"),
        "dataType": doc.get("dataType"),
        "allowedValues": doc.get("allowedValues", []),
    }

@blp.route("/")
class ParametersList(MethodView):
    # PUBLIC_INTERFACE
    def get(self):
        """List parameters with optional pagination: page, pageSize"""
        db = get_db()
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("pageSize", 50))
        if page < 1 or page_size < 1 or page_size > 500:
            raise ValidationError("Invalid pagination values", code=400)
        skip = (page - 1) * page_size
        cursor = db.parameters.find({}).sort("key", 1).skip(skip).limit(page_size)
        items = [_doc_to_dict(d) for d in cursor]
        total = db.parameters.count_documents({})
        return {"items": items, "page": page, "pageSize": page_size, "total": total}

@blp.route("/bulk")
class ParametersBulk(MethodView):
    # PUBLIC_INTERFACE
    def post(self):
        """Bulk upload parameters.
        Accepts JSON body: { items: [ { key, description?, dataType?, allowedValues? } ] }
        """
        db = get_db()
        payload = request.get_json(silent=True) or {}
        items = payload.get("items")
        if not isinstance(items, list) or not items:
            raise ValidationError("Body must include non-empty 'items' array", code=400)

        docs = []
        for i, item in enumerate(items):
            key = item.get("key")
            if not key or not isinstance(key, str):
                raise ValidationError(f"Item {i} missing 'key'", code=400)
            doc = {
                "key": key,
                "description": item.get("description"),
                "dataType": item.get("dataType"),
                "allowedValues": item.get("allowedValues") or [],
            }
            docs.append(doc)
        # Upsert by key
        for d in docs:
            db.parameters.update_one({"key": d["key"]}, {"$set": d}, upsert=True)
        return {"inserted": len(docs)}
