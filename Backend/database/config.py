from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "Gtwg")

class DataBase:
    client: AsyncIOMotorClient = None

db = DataBase()

async def connect_to_mongo():
    db.client = AsyncIOMotorClient(MONGO_URI)
    db.database = db.client[DB_NAME]
    print("✅ Connected to MongoDB")


async def close_mongo_connection():
    db.client.close()
    print("❌ MongoDB connection closed")