# app/db/mongodb.py
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from loguru import logger
from app.core.config import settings

client: Optional[AsyncIOMotorClient] = None
db: Optional[AsyncIOMotorDatabase] = None

async def get_database() -> AsyncIOMotorDatabase:
    global client, db
    if client is None:
        client = AsyncIOMotorClient(settings.MONGODB_URI)
        db = client.get_database(settings.MONGODB_DB)
        try:
            # Test the connection
            await client.admin.command('ping')
            logger.info("✅ Connected to MongoDB!")
            return db
        except Exception as e:
            logger.error(f"❌ Could not connect to MongoDB: {e}")
            raise
    return db

async def close_mongo_connection():
    global client
    if client is not None:
        client.close()
        client = None
        db = None