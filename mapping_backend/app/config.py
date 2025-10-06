import os
from dataclasses import dataclass


@dataclass
class MongoConfig:
    """MongoDB configuration loaded from environment variables."""
    uri: str
    db_name: str


def load_mongo_config() -> MongoConfig:
    """Load MongoDB configuration from environment variables.

    Required env vars:
    - MONGO_URI: Mongo connection string (mongodb://... or mongodb+srv://...)
    - MONGO_DB_NAME: Database name
    """
    uri = os.getenv("MONGO_URI")
    db = os.getenv("MONGO_DB_NAME")
    if not uri or not db:
        # Keep error message helpful for deployment orchestration
        raise RuntimeError(
            "Missing MongoDB configuration. "
            "Please set environment variables: MONGO_URI and MONGO_DB_NAME"
        )
    return MongoConfig(uri=uri, db_name=db)
