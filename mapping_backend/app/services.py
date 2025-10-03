from datetime import datetime
from typing import Dict, List, Optional, Tuple

from bson import ObjectId
from pymongo import ReturnDocument

from .db import get_db
from .errors import NotFoundError, ConflictError, ValidationError


def _oid(oid_str: str) -> ObjectId:
    try:
        return ObjectId(oid_str)
    except Exception:
        raise ValidationError("Invalid ID format")


# Vendor Services

def list_vendors() -> List[Dict]:
    db = get_db()
    vendors = list(db.vendors.find({}).sort("name", 1))
    return [_vendor_to_dict(v) for v in vendors]


def create_vendor(data: Dict) -> Dict:
    db = get_db()
    code = data.get("code")
    if db.vendors.find_one({"code": code}):
        raise ConflictError(f"Vendor with code '{code}' already exists")
    doc = {
        "name": data["name"],
        "code": data["code"],
        "description": data.get("description"),
        "is_active": data.get("is_active", True),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    res = db.vendors.insert_one(doc)
    doc["_id"] = res.inserted_id
    return _vendor_to_dict(doc)


def get_vendor(vendor_id: str) -> Dict:
    db = get_db()
    v = db.vendors.find_one({"_id": _oid(vendor_id)})
    if not v:
        raise NotFoundError("Vendor not found")
    return _vendor_to_dict(v)


def update_vendor(vendor_id: str, data: Dict) -> Dict:
    db = get_db()
    update = {k: v for k, v in data.items() if v is not None}
    if not update:
        return get_vendor(vendor_id)
    update["updated_at"] = datetime.utcnow()
    v = db.vendors.find_one_and_update(
        {"_id": _oid(vendor_id)},
        {"$set": update},
        return_document=ReturnDocument.AFTER
    )
    if not v:
        raise NotFoundError("Vendor not found")
    return _vendor_to_dict(v)


def delete_vendor(vendor_id: str) -> None:
    db = get_db()
    # Optional: check mappings exist and prevent deletion or cascade
    db.mappings.delete_many({"vendor_id": _oid(vendor_id)})
    db.mapping_history.delete_many({"vendor_id": _oid(vendor_id)})
    res = db.vendors.delete_one({"_id": _oid(vendor_id)})
    if res.deleted_count == 0:
        raise NotFoundError("Vendor not found")


def _vendor_to_dict(doc: Dict) -> Dict:
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "code": doc["code"],
        "description": doc.get("description"),
        "is_active": doc.get("is_active", True),
    }


# Mapping Services

def list_mappings(vendor_id: Optional[str] = None, namespace: Optional[str] = None) -> List[Dict]:
    db = get_db()
    query: Dict = {}
    if vendor_id:
        query["vendor_id"] = _oid(vendor_id)
    if namespace:
        query["namespace"] = namespace
    mappings = list(db.mappings.find(query).sort([("vendor_id", 1), ("namespace", 1)]))
    return [_mapping_to_dict(m) for m in mappings]


def create_mapping(data: Dict) -> Dict:
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


def get_mapping(mapping_id: str) -> Dict:
    db = get_db()
    m = db.mappings.find_one({"_id": _oid(mapping_id)})
    if not m:
        raise NotFoundError("Mapping not found")
    return _mapping_to_dict(m)


def update_mapping(mapping_id: str, data: Dict) -> Dict:
    db = get_db()
    m = db.mappings.find_one({"_id": _oid(mapping_id)})
    if not m:
        raise NotFoundError("Mapping not found")

    update = {}
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
        return_document=ReturnDocument.AFTER
    )
    _record_history(updated, "update", db)
    return _mapping_to_dict(updated)


def delete_mapping(mapping_id: str) -> None:
    db = get_db()
    m = db.mappings.find_one({"_id": _oid(mapping_id)})
    if not m:
        raise NotFoundError("Mapping not found")
    db.mappings.delete_one({"_id": m["_id"]})
    _record_history(m, "delete", db)


def _mapping_to_dict(doc: Dict) -> Dict:
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
    if db is None:
        db = get_db()
    hist = {
        "mapping_id": mapping_doc.get("_id") or _oid(mapping_doc["id"]),
        "vendor_id": mapping_doc["vendor_id"] if isinstance(mapping_doc["vendor_id"], ObjectId)
        else _oid(mapping_doc["vendor_id"]),
        "change_type": change_type,
        "version": mapping_doc.get("version", 1),
        "changed_at": datetime.utcnow(),
        "diff": {},  # Simplified; could store field-level diffs
    }
    db.mapping_history.insert_one(hist)


# History Services

def list_history(mapping_id: Optional[str] = None, vendor_id: Optional[str] = None) -> List[Dict]:
    db = get_db()
    q: Dict = {}
    if mapping_id:
        q["mapping_id"] = _oid(mapping_id)
    if vendor_id:
        q["vendor_id"] = _oid(vendor_id)
    records = list(db.mapping_history.find(q).sort("changed_at", -1))
    return [_history_to_dict(h) for h in records]


def _history_to_dict(doc: Dict) -> Dict:
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

def resolve_mapping(vendor_id: str, parameters: List[str], namespace: str = "default",
                    values: Optional[Dict] = None) -> Tuple[Dict, List[Dict]]:
    """Resolve vendor-specific mapping for given parameters.

    Returns:
      resolved map of output_param -> value (if provided/transformed),
      and the list of rules used.
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
        # For now, simple pass-through or identity transform; hook for future custom functions
        value = values.get(p)
        if transform:
            value = _apply_transform(transform, value)
        resolved[output_key] = value

    return resolved, m.get("rules", [])


def _apply_transform(transform: Optional[str], value):
    # Placeholder for extensible transform handling
    if not transform:
        return value
    if transform == "to_string" and value is not None:
        return str(value)
    if transform == "to_int":
        try:
            return int(value) if value is not None else None
        except Exception:
            return value
    # Unknown transforms: no-op
    return value
