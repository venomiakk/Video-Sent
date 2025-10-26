from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from typing import Optional, Literal


class TranscriptionRequest(BaseModel):
    url: HttpUrl
    model: Optional[Literal["whisperpy-tiny", "whisperpy-base", "whisperpy-small", "whisperpy-medium", "whisperpy-large", "whisperpy-turbo"]] = "whisperpy-base"

class Transcription(BaseModel):
    link_hash: str
    url: HttpUrl
    title: Optional[str]
    transcription: Optional[str]
    model: Optional[Literal["whisperpy-tiny", "whisperpy-base", "whisperpy-small", "whisperpy-medium", "whisperpy-large", "whisperpy-turbo"]]
    created_at: datetime
    id: Optional[str] = Field(None, alias="_id")
    # Maybe add video services, duration, transcription provider etc. later
    class Config:
        orm_mode = True
        allow_population_by_field_name = True