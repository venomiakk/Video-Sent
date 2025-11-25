from fastapi import APIRouter
from .schemas import TranscriptionRequest, Transcription
from .service import transcribe_video

router = APIRouter()

@router.post("/process")
async def process_video(request: TranscriptionRequest):
    '''
    Download and transcribe video from URL provided in request.\n
    Uses Deepgram's API for transcription with nova-2 model.
    '''
    result = await transcribe_video(request.url, model_name=request.model)
    return result