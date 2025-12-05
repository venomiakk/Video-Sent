from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import logging

# Importy Routerów
from app.modules.v1.transcription.router import router as transcribe_router
from app.modules.v1.sentiment.router import router as sentiment_router
from app.modules.v1.auth.router import router as auth_router

# Importy Core
from app.core.database import init_indexes
from app.core.exceptions import AppException
from app.socketio_handler import mount_socketio

from app.core.exception_handlers import (
    app_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    global_exception_handler
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_indexes()
    logger.info("✅ MongoDB connected and indexes initialized!")
    yield

app = FastAPI(title="Video Sentiment Analyzer", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mount_socketio(app)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication v1"])
app.include_router(transcribe_router, prefix="/api/v1/transcribe", tags=["Transcription v1"])
app.include_router(sentiment_router, prefix="/api/v1/sentiment", tags=["Sentiment Analysis v1"])

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

@app.get("/")
def root():
    return {"message": "Welcome to Video Sentiment Analyzer API 🚀"}

from app.modules.v1.transcription.schemas import TranscriptionRequest
from app.modules.v1.transcription.service import transcribe_video
from app.modules.v1.sentiment.service import analyze
@app.post("/api/v1/process")
async def process(request: TranscriptionRequest):
    result = await transcribe_video(request.url, model_name=request.model)
    string_id = str(result.id)
    analysis = await analyze(string_id)
    return {"transcription": result, "sentiment_analysis": analysis}