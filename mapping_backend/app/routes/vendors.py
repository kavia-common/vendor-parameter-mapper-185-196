from flask_smorest import Blueprint
from flask.views import MethodView
from flask import request

from ..schemas import VendorCreateSchema, VendorSchema, VendorUpdateSchema
from ..services import list_vendors, create_vendor, get_vendor, update_vendor, delete_vendor

blp = Blueprint("Vendors", "vendors", url_prefix="/vendors", description="CRUD for vendors")


@blp.route("/")
class VendorsList(MethodView):
    # PUBLIC_INTERFACE
    def get(self):
        """List vendors with pagination.
        Query params: page (default 1), pageSize (default 50)
        """
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("pageSize", 50))
        items, total = list_vendors(page=page, page_size=page_size)
        return {"items": items, "page": page, "pageSize": page_size, "total": total}

    # PUBLIC_INTERFACE
    @blp.arguments(VendorCreateSchema)
    @blp.response(201, VendorSchema)
    def post(self, json_data):
        """Create vendor.
        Expects VendorCreateSchema; returns created VendorSchema.
        """
        return create_vendor(json_data)


@blp.route("/<string:vendor_id>")
class VendorDetail(MethodView):
    # PUBLIC_INTERFACE
    @blp.response(200, VendorSchema)
    def get(self, vendor_id):
        """Get vendor by id."""
        return get_vendor(vendor_id)

    # PUBLIC_INTERFACE
    @blp.arguments(VendorUpdateSchema)
    @blp.response(200, VendorSchema)
    def patch(self, json_data, vendor_id):
        """Update vendor by id."""
        return update_vendor(vendor_id, json_data)

    # PUBLIC_INTERFACE
    def delete(self, vendor_id):
        """Delete vendor by id."""
        delete_vendor(vendor_id)
        return {"message": "Deleted"}
