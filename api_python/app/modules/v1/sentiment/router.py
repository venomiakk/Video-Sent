from fastapi import APIRouter
from .service import analyze

router = APIRouter()

@router.get("/")
def sentiment_test():
    return {"message": "Sentiment module is UP"}

@router.post("/analyze/{transcript_id}")
async def analyze_sentiment(transcript_id: str):
    """
    Analyze sentiment for a given transcription ID.\n
    Currently uses nltk for text processing and huggingface transformers for sentiment classification.
    """
    analysis_results = await analyze(transcript_id)

    return {"message": analysis_results}