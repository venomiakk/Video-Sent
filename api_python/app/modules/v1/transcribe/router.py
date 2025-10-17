from fastapi import APIRouter
from .schemas import TranscriptionRequest
from .service import transcribe_video

router = APIRouter()

@router.get("/")
def transcribe_test():
    return {"message": "Transcription module is UP"}

@router.post("/process")
def process_video(request: TranscriptionRequest):
    result = transcribe_video(request.url)
    return {"transcription": result}