from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# v1
from app.modules.v1.transcription.schemas import Transcription, TranscriptionRequest
from app.modules.v1.transcription.service import transcribe_video as transcribe_video_v1
from app.modules.v1.transcription.router import router as transcribe_router_v1
from app.modules.v1.sentiment.router import router as sentiment_router_v1
from app.modules.v1.sentiment.service import analyze as analyze_sentiment_v1
from app.modules.v1.auth.router import router as auth_router
# v2
from app.modules.v2.transcription.service import transcribe_video as transcribe_video_v2
from app.modules.v2.transcription.router import router as transcribe_router_v2
from app.modules.v2.sentiment.router import router as sentiment_router_v2
from app.modules.v2.sentiment.service import analyze as analyze_sentiment_v2

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

# v1
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication v1"])
app.include_router(transcribe_router_v1, prefix="/api/v1/transcribe", tags=["Transcription v1"])
app.include_router(sentiment_router_v1, prefix="/api/v1/sentiment", tags=["Sentiment Analysis v1"])

# v2
app.include_router(transcribe_router_v2, prefix="/api/v2/transcribe", tags=["Transcription v2"])
app.include_router(sentiment_router_v2, prefix="/api/v2/sentiment", tags=["Sentiment Analysis v2"])

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
    result = await transcribe_video_v1(request.url, model_name=request.model)
    string_id = str(result.id)
    analysis = await analyze_sentiment_v1(string_id)
    return {"transcription": result, "sentiment_analysis": analysis}