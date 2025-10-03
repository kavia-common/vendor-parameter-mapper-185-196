from marshmallow import Schema, fields, validate


class VendorBaseSchema(Schema):
    name = fields.Str(required=True, description="Vendor name", validate=validate.Length(min=1))
    code = fields.Str(required=True, description="Unique vendor code", validate=validate.Length(min=1))
    description = fields.Str(required=False, allow_none=True, load_default=None, description="Optional description")
    is_active = fields.Bool(required=False, load_default=True, description="Active flag")


class VendorCreateSchema(VendorBaseSchema):
    pass


class VendorUpdateSchema(Schema):
    name = fields.Str(required=False, description="Vendor name", validate=validate.Length(min=1))
    description = fields.Str(required=False, allow_none=True, load_default=None, description="Optional description")
    is_active = fields.Bool(required=False, description="Active flag")


class VendorSchema(VendorBaseSchema):
    id = fields.Str(required=True, description="Vendor ID")


class MappingRuleBase(Schema):
    """Represents a single input->output mapping rule."""
    input_param = fields.Str(required=True, description="Source parameter name")
    output_param = fields.Str(required=True, description="Target parameter name for this vendor")
    transform = fields.Str(required=False, allow_none=True, load_default=None,
                           description="Optional transform name or expression")


class ParameterMappingCreateSchema(Schema):
    vendor_id = fields.Str(required=True, description="Vendor ID the mapping belongs to")
    namespace = fields.Str(required=False, load_default="default", description="Optional logical namespace")
    rules = fields.List(fields.Nested(MappingRuleBase), required=True, description="List of mapping rules")


class ParameterMappingUpdateSchema(Schema):
    namespace = fields.Str(required=False, description="Logical namespace")
    rules = fields.List(fields.Nested(MappingRuleBase), required=False, description="List of mapping rules")


class ParameterMappingSchema(Schema):
    id = fields.Str(required=True, description="Mapping ID")
    vendor_id = fields.Str(required=True, description="Vendor ID")
    namespace = fields.Str(required=True, description="Namespace")
    rules = fields.List(fields.Nested(MappingRuleBase), required=True, description="Rules")
    version = fields.Int(required=True, description="Version number")
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)


class MappingHistorySchema(Schema):
    id = fields.Str(required=True, description="History record ID")
    mapping_id = fields.Str(required=True, description="Related mapping ID")
    vendor_id = fields.Str(required=True, description="Vendor ID")
    change_type = fields.Str(required=True, description="Type of change (create, update, delete)")
    version = fields.Int(required=True, description="Mapping version after change")
    changed_at = fields.DateTime(required=True)
    diff = fields.Dict(required=False, description="Optional diff data")


class QueryResolutionRequest(Schema):
    vendor_id = fields.Str(required=True, description="Vendor ID")
    namespace = fields.Str(required=False, load_default="default", description="Namespace to resolve in")
    parameters = fields.List(fields.Str(), required=True, description="List of source parameter names")
    values = fields.Dict(keys=fields.Str(), values=fields.Raw(), required=False,
                         description="Optional parameter values for transform usage")


class QueryResolutionResult(Schema):
    vendor_id = fields.Str(required=True)
    namespace = fields.Str(required=True)
    resolved = fields.Dict(keys=fields.Str(), values=fields.Raw(), required=True,
                           description="Mapping of output parameters to provided values or transformed values")
    rules_used = fields.List(fields.Nested(MappingRuleBase), required=True)
