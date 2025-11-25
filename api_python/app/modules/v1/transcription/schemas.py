from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from typing import Optional, Literal


class TranscriptionRequest(BaseModel):
    url: HttpUrl
    model: Optional[Literal["deepgram-nova-2"]] = "deepgram-nova-2"

class Transcription(BaseModel):
    link_hash: str
    url: HttpUrl
    title: Optional[str]
    transcription: Optional[str]
    model: Optional[Literal["deepgram-nova-2"]]
    created_at: datetime
    id: Optional[str] = Field(None, alias="_id")
    # Maybe add video services, duration, transcription provider etc. later
    class Config:
        orm_mode = True
        allow_population_by_field_name = True