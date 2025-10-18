from fastapi import FastAPI
from app.modules.v1.transcription.router import router as transcribe_router
from app.modules.v1.sentiment.router import router as sentiment_router
from app.core.database import init_indexes
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import AppException


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # startup: initialize database indexes (or other resources)
    await init_indexes()
    print("✅ MongoDB connected and indexes initialized!")
    try:
        yield
    finally:
        # shutdown: place any cleanup here, e.g. close db connections if needed
        # if hasattr(db, "close"):
        #     await db.close()
        pass


app = FastAPI(title="Video Sentiment Analyzer", lifespan=lifespan)

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