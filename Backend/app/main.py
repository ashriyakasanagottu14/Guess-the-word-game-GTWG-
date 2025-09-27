from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.db.mongodb import get_database
from app.db.indexes import ensure_indexes
from app.db.seed_words import seed_initial_words
from app.db.seed_admin import ensure_default_admin
from app.api.routers.auth import router as auth_router
from app.api.routers.game import router as game_router
from app.api.routers.admin import router as admin_router

app = FastAPI(title=settings.APP_NAME, debug=settings.APP_DEBUG)

# Configure CORS
origins = [
    "http://127.0.0.1:5500",  # VS Code Live Server
    "http://localhost:5500",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://localhost",
    "file://",  # For local file access
    "null",     # For local file access
    "*"  # Allow all origins during development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["Content-Type", "Authorization"]
)

app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(game_router, prefix=settings.API_PREFIX)
app.include_router(admin_router, prefix=settings.API_PREFIX)

@app.on_event("startup")
async def on_startup():
    logger.info("Starting up application...")
    try:
        db = await get_database()
        await ensure_indexes()
        await seed_initial_words()
        await ensure_default_admin()  # Ensure default admin user exists
        logger.info("✅ Startup complete")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise