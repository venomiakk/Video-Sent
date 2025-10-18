from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
from fastapi import FastAPI

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "video_sentiment"

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

async def init_indexes():
    await db.transcriptions.create_index("link_hash")
    await db.transcriptions.create_index("created_at")

    # await db.sentiments.create_index("transcription_id")