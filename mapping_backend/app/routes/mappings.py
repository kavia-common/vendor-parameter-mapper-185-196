from flask_smorest import Blueprint
from flask.views import MethodView
from flask import request

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
)

blp = Blueprint("Mappings", "mappings", url_prefix="/mappings", description="CRUD for parameter mappings")


@blp.route("/")
class MappingsList(MethodView):
    # PUBLIC_INTERFACE
    def get(self):
        """List mappings.
        Optional query parameters: vendor_id, namespace
        """
        vendor_id = request.args.get("vendor_id")
        namespace = request.args.get("namespace")
        return {"items": list_mappings(vendor_id=vendor_id, namespace=namespace)}

    # PUBLIC_INTERFACE
    @blp.arguments(ParameterMappingCreateSchema)
    @blp.response(201, ParameterMappingSchema)
    def post(self, json_data):
        """Create mapping for vendor and namespace."""
        return create_mapping(json_data)


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
