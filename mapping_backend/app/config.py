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
    - MONGODB_URL: Mongo connection string (mongodb://... or mongodb+srv://...)
    - MONGODB_DB: Database name
    """
    uri = os.getenv("MONGODB_URL")
    db = os.getenv("MONGODB_DB")
    if not uri or not db:
        # Keep error message helpful for deployment orchestration
        raise RuntimeError(
            "Missing MongoDB configuration. "
            "Please set environment variables: MONGODB_URL and MONGODB_DB"
        )
    return MongoConfig(uri=uri, db_name=db)
