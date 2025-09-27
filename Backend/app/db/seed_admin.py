from bson import ObjectId
from loguru import logger

from app.core.security import get_password_hash
from app.core.roles import ADMIN


async def ensure_default_admin():
    """Ensure the default admin user exists with the specified credentials."""
    from app.db.mongodb import get_database
    
    db = await get_database()
    admin_username = "admin_game"
    admin_password = "secretcode"
    
    # Check if admin already exists
    admin = await db.users.find_one({"username": admin_username, "role": ADMIN})
    
    if admin:
        logger.info("✅ Admin user already exists")
        return
    
    # Create admin user
    admin_data = {
        "username": admin_username,
        "hashed_password": get_password_hash(admin_password),
        "role": ADMIN,
        "created_at": ObjectId().generation_time
    }
    
    result = await db.users.insert_one(admin_data)
    if result.inserted_id:
        logger.info(f"✅ Created default admin user with username: {admin_username}")
    else:
        logger.error("❌ Failed to create default admin user")
