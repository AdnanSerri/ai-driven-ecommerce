"""
Database clients for the ML microservice.
"""

from database.mongodb import get_mongodb, close_mongodb, MongoDBClient
from database.postgres import get_postgres, close_postgres, PostgresClient
from database.weaviate_client import get_weaviate, close_weaviate, WeaviateClient
from database.redis_client import get_redis, close_redis, RedisClient

# Interaction logging (PostgreSQL-backed)
from database.interaction_client import (
    get_interaction_client,
    close_interaction_client,
    InteractionClient,
    is_interaction_client_available,
)

__all__ = [
    "get_mongodb",
    "close_mongodb",
    "MongoDBClient",
    "get_postgres",
    "close_postgres",
    "PostgresClient",
    "get_weaviate",
    "close_weaviate",
    "WeaviateClient",
    "get_interaction_client",
    "close_interaction_client",
    "InteractionClient",
    "is_interaction_client_available",
    "get_redis",
    "close_redis",
    "RedisClient",
]
