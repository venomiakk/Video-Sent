from fastapi import APIRouter
from .schemas import TranscriptionRequest, Transcription
from .service import transcribe_video

router = APIRouter()

@router.get("/")
def transcribe_test():
    return {"message": "Transcription module is UP"}

@router.post("/process", response_model=Transcription)
async def process_video(request: TranscriptionRequest):
    '''
    Download and transcribe video from URL provided in request.\n
    Uses python's openai-whisper.
    '''
    result = await transcribe_video(request.url, model_name=request.model)
    return result