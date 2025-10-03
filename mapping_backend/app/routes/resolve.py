from flask_smorest import Blueprint
from flask.views import MethodView

from ..schemas import QueryResolutionRequest, QueryResolutionResult
from ..services import resolve_mapping

blp = Blueprint("Resolve", "resolve", url_prefix="/resolve", description="Resolve vendor mapping for parameter list")


@blp.route("/")
class Resolve(MethodView):
    # PUBLIC_INTERFACE
    @blp.arguments(QueryResolutionRequest)
    @blp.response(200, QueryResolutionResult)
    def post(self, json_data):
        """Resolve mapping for a vendor and parameter list.
        Request: vendor_id, namespace (optional, default 'default'), parameters [list of input param names], values (optional dict)
        Returns: mapping of output_param -> value, and rules used.
        """
        resolved, rules = resolve_mapping(
            vendor_id=json_data["vendor_id"],
            parameters=json_data["parameters"],
            namespace=json_data.get("namespace", "default"),
            values=json_data.get("values") or {},
        )
        return {
            "vendor_id": json_data["vendor_id"],
            "namespace": json_data.get("namespace", "default"),
            "resolved": resolved,
            "rules_used": rules,
        }
