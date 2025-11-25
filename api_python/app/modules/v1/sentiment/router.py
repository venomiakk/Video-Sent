from fastapi import APIRouter
from .service import analyze

router = APIRouter()

@router.post("/analyze/{transcript_id}")
async def analyze_sentiment(transcript_id: str):
    """
    Analyze sentiment for a given transcription ID.\n
    Currently uses Groq API with llama3-70b-8192 model.
    """
    analysis_results = await analyze(transcript_id)
    return {"message": analysis_results}