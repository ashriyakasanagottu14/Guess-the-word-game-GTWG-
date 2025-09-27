# app/db/seed_words.py
from datetime import datetime, timezone
from loguru import logger
from app.db.mongodb import get_database

WORDS = [
    "APPLE", "BERRY", "CANDY", "DELTA", "EAGLE",
    "FLAME", "GIANT", "HOTEL", "IVORY", "JELLY",
    "KNIFE", "LEMON", "MANGO", "NINJA", "OPERA",
    "PARTY", "QUEEN", "RIVER", "SUSHI", "TIGER",
]

async def seed_initial_words():
    try:
        db = await get_database()
        count = await db.words.count_documents({})
        if count >= 20:
            logger.info("✅ Database already seeded")
            return

        existing_words = set()
        async for word in db.words.find({}, {"text": 1}):
            existing_words.add(word["text"])

        to_insert = [
            {"text": w, "active": True, "created_at": datetime.now(timezone.utc)}
            for w in WORDS if w not in existing_words
        ]

        if to_insert:
            await db.words.insert_many(to_insert)
            logger.info(f"✅ Seeded {len(to_insert)} words")
    except Exception as e:
        logger.error(f"❌ Failed to seed words: {e}")
        raise