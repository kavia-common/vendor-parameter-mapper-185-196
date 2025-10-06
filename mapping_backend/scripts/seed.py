#!/usr/bin/env python3
"""
Seed script to insert sample vendors, parameters, and mappings for quick preview.
Run: python scripts/seed.py
Environment: requires MONGO_URI and MONGO_DB_NAME
"""
from datetime import datetime
from bson import ObjectId
from app.config import load_mongo_config
from pymongo import MongoClient

def main():
    cfg = load_mongo_config()
    client = MongoClient(cfg.uri)
    db = client[cfg.db_name]

    # Vendors
    vendor = db.vendors.find_one({"code": "ACME"})
    if not vendor:
        vendor_id = db.vendors.insert_one({
            "name": "ACME Corp",
            "code": "ACME",
            "description": "Sample vendor",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }).inserted_id
    else:
        vendor_id = vendor["_id"]

    # Parameters
    params = [
        {"key": "first_name", "description": "First Name", "dataType": "string"},
        {"key": "last_name", "description": "Last Name", "dataType": "string"},
        {"key": "age", "description": "Age", "dataType": "int"},
    ]
    for p in params:
        db.parameters.update_one({"key": p["key"]}, {"$set": p}, upsert=True)

    # Mapping (default namespace)
    mapping = db.mappings.find_one({"vendor_id": vendor_id, "namespace": "default"})
    rules = [
        {"input_param": "first_name", "output_param": "fname", "transform": "uppercase"},
        {"input_param": "last_name", "output_param": "lname"},
        {"input_param": "age", "output_param": "age_years", "transform": "to_int"},
    ]
    now = datetime.utcnow()
    if not mapping:
        db.mappings.insert_one({
            "vendor_id": vendor_id,
            "namespace": "default",
            "rules": rules,
            "version": 1,
            "created_at": now,
            "updated_at": now,
        })
    else:
        db.mappings.update_one({"_id": mapping["_id"]}, {"$set": {"rules": rules, "updated_at": now}})

    print("Seed complete.")

if __name__ == "__main__":
    main()
