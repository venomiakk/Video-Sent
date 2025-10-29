from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.modules.v1.transcription.schemas import Transcription, TranscriptionRequest
from app.modules.v1.transcription.service import transcribe_video
from app.modules.v1.transcription.router import router as transcribe_router
from app.modules.v1.sentiment.router import analyze_sentiment, router as sentiment_router
from app.modules.v1.auth.router import router as auth_router
from app.core.database import init_indexes
from app.socketio_handler import mount_socketio
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import AppException
import logging

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # startup: initialize database indexes (or other resources)
    await init_indexes()
    logging.info("✅ MongoDB connected and indexes initialized!")
    try:
        yield
    finally:
        # shutdown: place any cleanup here, e.g. close db connections if needed
        # if hasattr(db, "close"):
        #     await db.close()
        pass


app = FastAPI(title="Video Sentiment Analyzer", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Socket.IO
mount_socketio(app)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(transcribe_router, prefix="/api/v1/transcribe", tags=["Transcription"])
app.include_router(sentiment_router, prefix="/api/v1/sentiment", tags=["Sentiment"])


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


@app.get("/")
def root():
    """
    Default GET method
    """
    return {"message": "Welcome to Video Sentiment Analyzer API 🚀"}

@app.post("/api/v1/process")
async def process(request: TranscriptionRequest):
    """
    Main method for sentiment analysis
    """
    result = await transcribe_video(request.url, model_name=request.model)
    string_id = str(result.id)
    analysis = await analyze_sentiment(string_id)
    return {"transcription": result, "sentiment_analysis": analysis}