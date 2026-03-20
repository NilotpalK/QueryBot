import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

_client: AsyncIOMotorClient | None = None


def get_db() -> AsyncIOMotorDatabase:
    """Return the shared async MongoDB database (lazy singleton)."""
    global _client
    if _client is None:
        uri = os.getenv("MONGODB_URI", "")
        if not uri:
            raise RuntimeError("MONGODB_URI environment variable is not set")
        _client = AsyncIOMotorClient(uri)
    return _client["querybot"]
