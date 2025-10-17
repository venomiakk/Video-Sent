from pydantic import BaseModel, HttpUrl

class TranscriptionRequest(BaseModel):
    url: HttpUrl
