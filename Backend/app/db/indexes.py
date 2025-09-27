# app/db/indexes.py
from app.db.mongodb import get_database

async def ensure_indexes():
    db = await get_database()
    await db.users.create_index("username", unique=True)
    await db.words.create_index("text", unique=True)
    await db.games.create_index([("user_id", 1), ("started_at", 1)])