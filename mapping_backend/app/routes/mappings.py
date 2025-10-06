from flask_smorest import Blueprint
from flask.views import MethodView
from flask import request
import csv
import io
import json

from ..schemas import (
    ParameterMappingCreateSchema,
    ParameterMappingSchema,
    ParameterMappingUpdateSchema,
)
from ..services import (
    list_mappings,
    create_mapping,
    get_mapping,
    update_mapping,
    delete_mapping,
    bulk_upsert_mappings,
)

blp = Blueprint("Mappings", "mappings", url_prefix="/mappings", description="CRUD for parameter mappings")


@blp.route("/")
class MappingsList(MethodView):
    # PUBLIC_INTERFACE
    def get(self):
        """List mappings with pagination.
        Optional query parameters: vendorId, namespace, page, pageSize
        """
        vendor_id = request.args.get("vendorId")
        namespace = request.args.get("namespace")
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("pageSize", 50))
        items, total = list_mappings(vendor_id=vendor_id, namespace=namespace, page=page, page_size=page_size)
        return {"items": items, "page": page, "pageSize": page_size, "total": total}

    # PUBLIC_INTERFACE
    @blp.arguments(ParameterMappingCreateSchema)
    @blp.response(201, ParameterMappingSchema)
    def post(self, json_data):
        """Create mapping for vendor and namespace."""
        return create_mapping(json_data)


@blp.route("/bulk")
class MappingsBulk(MethodView):
    # PUBLIC_INTERFACE
    def post(self):
        """Bulk upload mappings.
        Accepts JSON body:
        { items: [ { vendor_id, namespace?, rules: [ {input_param, output_param, transform?} ] } ] }
        Or CSV upload (Content-Type text/csv or multipart form) with columns:
        vendor_id,namespace,input_param,output_param,transform
        """
        content_type = request.content_type or ""
        if "text/csv" in content_type:
            data = request.get_data(as_text=True)
            reader = csv.DictReader(io.StringIO(data))
            items = {}
            for row in reader:
                vid = row.get("vendor_id")
                ns = row.get("namespace") or "default"
                key = f"{vid}:{ns}"
                items.setdefault(key, {"vendor_id": vid, "namespace": ns, "rules": []})
                items[key]["rules"].append({
                    "input_param": row.get("input_param"),
                    "output_param": row.get("output_param"),
                    "transform": row.get("transform") or None
                })
            payload = list(items.values())
            count = bulk_upsert_mappings(payload)
            return {"processed": count}
        # JSON or multipart-json
        try:
            body = request.get_json(silent=True) or {}
        except Exception:
            body = {}
        if "items" not in body or not isinstance(body["items"], list):
            # try to parse multipart field 'file' as csv
            if "multipart/form-data" in content_type and "file" in request.files:
                file_storage = request.files["file"]
                text = file_storage.stream.read().decode("utf-8")
                reader = csv.DictReader(io.StringIO(text))
                items = {}
                for row in reader:
                    vid = row.get("vendor_id")
                    ns = row.get("namespace") or "default"
                    key = f"{vid}:{ns}"
                    items.setdefault(key, {"vendor_id": vid, "namespace": ns, "rules": []})
                    items[key]["rules"].append({
                        "input_param": row.get("input_param"),
                        "output_param": row.get("output_param"),
                        "transform": row.get("transform") or None
                    })
                payload = list(items.values())
                count = bulk_upsert_mappings(payload)
                return {"processed": count}
            return {"processed": 0}
        count = bulk_upsert_mappings(body["items"])
        return {"processed": count}


@blp.route("/<string:mapping_id>")
class MappingDetail(MethodView):
    # PUBLIC_INTERFACE
    @blp.response(200, ParameterMappingSchema)
    def get(self, mapping_id):
        """Get mapping by id."""
        return get_mapping(mapping_id)

    # PUBLIC_INTERFACE
    @blp.arguments(ParameterMappingUpdateSchema)
    @blp.response(200, ParameterMappingSchema)
    def patch(self, json_data, mapping_id):
        """Update mapping by id (rules and/or namespace)."""
        return update_mapping(mapping_id, json_data)

    # PUBLIC_INTERFACE
    def delete(self, mapping_id):
        """Delete mapping by id."""
        delete_mapping(mapping_id)
        return {"message": "Deleted"}
