from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional, Literal


class TranscriptionRequest(BaseModel):
    url: HttpUrl
    model: Optional[Literal["tiny", "base", "small", "medium", "large", "turbo"]] = "base"

class Transcription(BaseModel):
    link_hash: str
    url: HttpUrl
    title: Optional[str]
    transcription: Optional[str]
    model: Optional[Literal["tiny", "base", "small", "medium", "large", "turbo"]]
    created_at: datetime
    # Maybe add video services, duration, transcription provider etc. later
    class Config:
        orm_mode = True