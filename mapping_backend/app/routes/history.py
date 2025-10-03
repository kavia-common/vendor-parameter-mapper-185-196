from flask_smorest import Blueprint
from flask.views import MethodView
from flask import request

from ..services import list_history

blp = Blueprint("History", "history", url_prefix="/history", description="Mapping change history")


@blp.route("/")
class HistoryList(MethodView):
    # PUBLIC_INTERFACE
    def get(self):
        """List mapping history.
        Optional query parameters: mapping_id, vendor_id
        """
        mapping_id = request.args.get("mapping_id")
        vendor_id = request.args.get("vendor_id")
        return {"items": list_history(mapping_id=mapping_id, vendor_id=vendor_id)}
