from fastapi import FastAPI
from app.modules.v1.transcribe.router import router as transcribe_router
from app.modules.v1.sentiment.router import router as sentiment_router

app = FastAPI(title="Video Sentiment Analyzer")

app.include_router(transcribe_router, prefix="/api/v1/transcribe", tags=["Transcription"])
app.include_router(sentiment_router, prefix="/api/v1/sentiment", tags=["Sentiment"])


@app.get("/")
def root():
    '''
    Default GET method
    '''
    return {"message": "Welcome to Video Sentiment Analyzer API 🚀"}