from pymongo import MongoClient
from pymongo.errors import PyMongoError
from flask import g
from .config import load_mongo_config


def get_mongo_client() -> MongoClient:
    """Get or create a MongoClient stored in Flask app context."""
    if "mongo_client" not in g:
        cfg = load_mongo_config()
        try:
            g.mongo_client = MongoClient(cfg.uri)
        except PyMongoError as e:
            raise RuntimeError(f"Failed to connect to MongoDB: {e}") from e
    return g.mongo_client


def get_db():
    """Get database handle using configured DB name."""
    client = get_mongo_client()
    cfg = load_mongo_config()
    return client[cfg.db_name]


def teardown_mongo_client(exception=None):
    """Close client on app context teardown."""
    client = g.pop("mongo_client", None)
    if client is not None:
        client.close()
