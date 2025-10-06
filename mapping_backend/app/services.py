from datetime import datetime
from typing import Dict, List, Optional, Tuple

from bson import ObjectId
from pymongo import ReturnDocument

from .db import get_db
from .errors import NotFoundError, ConflictError, ValidationError


def _oid(oid_str: str) -> ObjectId:
    """Convert a string to ObjectId with validation."""
    try:
        return ObjectId(oid_str)
    except Exception:
        raise ValidationError("Invalid ID format")


# Vendor Services

# PUBLIC_INTERFACE
def list_vendors(page: int = 1, page_size: int = 50) -> Tuple[List[Dict], int]:
    """List vendors with pagination and return (items, total)."""
    db = get_db()
    if page < 1 or page_size < 1 or page_size > 500:
        raise ValidationError("Invalid pagination values", code=400)
    skip = (page - 1) * page_size
    cursor = db.vendors.find({}).sort("name", 1).skip(skip).limit(page_size)
    items = [_vendor_to_dict(v) for v in cursor]
    total = db.vendors.count_documents({})
    return items, total


def create_vendor(data: Dict) -> Dict:
    """Create a new vendor document."""
    db = get_db()
    code = data.get("code")
    if db.vendors.find_one({"code": code}):
        raise ConflictError(f"Vendor with code '{code}' already exists")
    now = datetime.utcnow()
    doc = {
        "name": data["name"],
        "code": data["code"],
        "description": data.get("description"),
        "is_active": data.get("is_active", True),
        "created_at": now,
        "updated_at": now,
    }
    res = db.vendors.insert_one(doc)
    doc["_id"] = res.inserted_id
    return _vendor_to_dict(doc)


def get_vendor(vendor_id: str) -> Dict:
    """Fetch a vendor by id."""
    db = get_db()
    v = db.vendors.find_one({"_id": _oid(vendor_id)})
    if not v:
        raise NotFoundError("Vendor not found")
    return _vendor_to_dict(v)


def update_vendor(vendor_id: str, data: Dict) -> Dict:
    """Patch vendor fields."""
    db = get_db()
    update = {k: v for k, v in data.items() if v is not None}
    if not update:
        return get_vendor(vendor_id)
    update["updated_at"] = datetime.utcnow()
    v = db.vendors.find_one_and_update(
        {"_id": _oid(vendor_id)},
        {"$set": update},
        return_document=ReturnDocument.AFTER,
    )
    if not v:
        raise NotFoundError("Vendor not found")
    return _vendor_to_dict(v)


def delete_vendor(vendor_id: str) -> None:
    """Delete a vendor and related mappings/history."""
    db = get_db()
    db.mappings.delete_many({"vendor_id": _oid(vendor_id)})
    db.mapping_history.delete_many({"vendor_id": _oid(vendor_id)})
    res = db.vendors.delete_one({"_id": _oid(vendor_id)})
    if res.deleted_count == 0:
        raise NotFoundError("Vendor not found")


def _vendor_to_dict(doc: Dict) -> Dict:
    """Serialize vendor document."""
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "code": doc["code"],
        "description": doc.get("description"),
        "is_active": doc.get("is_active", True),
    }


# Mapping Services

# PUBLIC_INTERFACE
def list_mappings(
    vendor_id: Optional[str] = None,
    namespace: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> Tuple[List[Dict], int]:
    """List mappings with optional filters and pagination; returns (items, total)."""
    db = get_db()
    if page < 1 or page_size < 1 or page_size > 500:
        raise ValidationError("Invalid pagination values", code=400)
    query: Dict = {}
    if vendor_id:
        query["vendor_id"] = _oid(vendor_id)
    if namespace:
        query["namespace"] = namespace
    skip = (page - 1) * page_size
    cursor = (
        db.mappings.find(query)
        .sort([("vendor_id", 1), ("namespace", 1)])
        .skip(skip)
        .limit(page_size)
    )
    items = [_mapping_to_dict(m) for m in cursor]
    total = db.mappings.count_documents(query)
    return items, total


def create_mapping(data: Dict) -> Dict:
    """Create a new mapping for a vendor and optional namespace."""
    db = get_db()
    vendor_oid = _oid(data["vendor_id"])
    if not db.vendors.find_one({"_id": vendor_oid}):
        raise NotFoundError("Vendor not found")

    namespace = data.get("namespace", "default")
    existing = db.mappings.find_one({"vendor_id": vendor_oid, "namespace": namespace})
    if existing:
        raise ConflictError("Mapping already exists for this vendor and namespace")

    now = datetime.utcnow()
    doc = {
        "vendor_id": vendor_oid,
        "namespace": namespace,
        "rules": data["rules"],
        "version": 1,
        "created_at": now,
        "updated_at": now,
    }
    res = db.mappings.insert_one(doc)
    doc["_id"] = res.inserted_id
    _record_history(doc, "create", db)
    return _mapping_to_dict(doc)


# PUBLIC_INTERFACE
def bulk_upsert_mappings(items: List[Dict]) -> int:
    """Upsert multiple mappings; replaces rules if mapping exists and bumps version."""
    db = get_db()
    processed = 0
    now = datetime.utcnow()
    for item in items:
        try:
            vendor_oid = _oid(item["vendor_id"])
        except ValidationError:
            continue
        if not db.vendors.find_one({"_id": vendor_oid}):
            # Skip if vendor doesn't exist
            continue
        namespace = item.get("namespace", "default")
        rules = item.get("rules") or []
        existing = db.mappings.find_one({"vendor_id": vendor_oid, "namespace": namespace})
        if existing:
            update = {
                "rules": rules,
                "version": int(existing.get("version", 1)) + 1,
                "updated_at": now,
            }
            updated = db.mappings.find_one_and_update(
                {"_id": existing["_id"]},
                {"$set": update},
                return_document=ReturnDocument.AFTER,
            )
            _record_history(updated, "update", db)
        else:
            doc = {
                "vendor_id": vendor_oid,
                "namespace": namespace,
                "rules": rules,
                "version": 1,
                "created_at": now,
                "updated_at": now,
            }
            res = db.mappings.insert_one(doc)
            doc["_id"] = res.inserted_id
            _record_history(doc, "create", db)
        processed += 1
    return processed


def get_mapping(mapping_id: str) -> Dict:
    """Get mapping by id."""
    db = get_db()
    m = db.mappings.find_one({"_id": _oid(mapping_id)})
    if not m:
        raise NotFoundError("Mapping not found")
    return _mapping_to_dict(m)


def update_mapping(mapping_id: str, data: Dict) -> Dict:
    """Patch mapping (namespace and/or rules)."""
    db = get_db()
    m = db.mappings.find_one({"_id": _oid(mapping_id)})
    if not m:
        raise NotFoundError("Mapping not found")

    update: Dict = {}
    if "namespace" in data and data["namespace"]:
        update["namespace"] = data["namespace"]
    if "rules" in data and data["rules"] is not None:
        update["rules"] = data["rules"]

    if not update:
        return _mapping_to_dict(m)

    update["version"] = m.get("version", 1) + 1
    update["updated_at"] = datetime.utcnow()

    updated = db.mappings.find_one_and_update(
        {"_id": m["_id"]},
        {"$set": update},
        return_document=ReturnDocument.AFTER,
    )
    _record_history(updated, "update", db)
    return _mapping_to_dict(updated)


def delete_mapping(mapping_id: str) -> None:
    """Delete mapping by id and record history."""
    db = get_db()
    m = db.mappings.find_one({"_id": _oid(mapping_id)})
    if not m:
        raise NotFoundError("Mapping not found")
    db.mappings.delete_one({"_id": m["_id"]})
    _record_history(m, "delete", db)


def _mapping_to_dict(doc: Dict) -> Dict:
    """Serialize mapping document."""
    return {
        "id": str(doc["_id"]),
        "vendor_id": str(doc["vendor_id"]),
        "namespace": doc.get("namespace", "default"),
        "rules": doc.get("rules", []),
        "version": doc.get("version", 1),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


def _record_history(mapping_doc: Dict, change_type: str, db=None):
    """Insert a history record for a mapping change."""
    if db is None:
        db = get_db()
    hist = {
        "mapping_id": mapping_doc.get("_id") or _oid(mapping_doc["id"]),
        "vendor_id": mapping_doc["vendor_id"]
        if isinstance(mapping_doc["vendor_id"], ObjectId)
        else _oid(mapping_doc["vendor_id"]),
        "change_type": change_type,
        "version": mapping_doc.get("version", 1),
        "changed_at": datetime.utcnow(),
        "diff": {},
    }
    db.mapping_history.insert_one(hist)


# History Services

# PUBLIC_INTERFACE
def list_history(mapping_id: Optional[str] = None, vendor_id: Optional[str] = None) -> List[Dict]:
    """List history records with optional filters."""
    db = get_db()
    q: Dict = {}
    if mapping_id:
        q["mapping_id"] = _oid(mapping_id)
    if vendor_id:
        q["vendor_id"] = _oid(vendor_id)
    records = list(db.mapping_history.find(q).sort("changed_at", -1))
    return [_history_to_dict(h) for h in records]


def _history_to_dict(doc: Dict) -> Dict:
    """Serialize history document."""
    return {
        "id": str(doc["_id"]),
        "mapping_id": str(doc["mapping_id"]),
        "vendor_id": str(doc["vendor_id"]),
        "change_type": doc["change_type"],
        "version": int(doc.get("version", 1)),
        "changed_at": doc.get("changed_at"),
        "diff": doc.get("diff", {}),
    }


# Query Resolution

# PUBLIC_INTERFACE
def resolve_mapping(
    vendor_id: str,
    parameters: List[str],
    namespace: str = "default",
    values: Optional[Dict] = None,
) -> Tuple[Dict, List[Dict]]:
    """Resolve vendor-specific mapping for given parameters.

    Returns:
      - resolved: dict of output_param -> value (if provided/transformed)
      - rules_used: list of rules considered
    """
    db = get_db()
    v = db.vendors.find_one({"_id": _oid(vendor_id), "is_active": True})
    if not v:
        raise NotFoundError("Active vendor not found")

    m = db.mappings.find_one({"vendor_id": v["_id"], "namespace": namespace})
    if not m:
        raise NotFoundError("Mapping not found for the vendor and namespace")

    values = values or {}
    rules_used: List[Dict] = []
    resolved: Dict = {}

    # Build lookup for quick resolution
    rule_by_input = {r["input_param"]: r for r in m.get("rules", [])}

    for p in parameters:
        rule = rule_by_input.get(p)
        if not rule:
            continue
        rules_used.append(rule)
        output_key = rule["output_param"]
        transform = rule.get("transform")
        value = values.get(p)
        if transform:
            value = _apply_transform(transform, value)
        resolved[output_key] = value

    return resolved, m.get("rules", [])


def _apply_transform(transform: Optional[str], value):
    """Apply simple transforms: to_string, to_int, uppercase, lowercase, constant:VAL, default:VAL."""
    if not transform:
        return value
    t = str(transform).strip().lower()
    if t == "to_string" and value is not None:
        return str(value)
    if t == "to_int":
        try:
            return int(value) if value is not None else None
        except Exception:
            return value
    if t == "uppercase" and isinstance(value, str):
        return value.upper()
    if t == "lowercase" and isinstance(value, str):
        return value.lower()
    if t.startswith("constant:"):
        return transform.split("constant:", 1)[1]
    if t.startswith("default:"):
        default_val = transform.split("default:", 1)[1]
        if value is None or value == "":
            return default_val
        return value
    # Unknown transforms: no-op
    return value
