from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class AnalysisStep(BaseModel):
    step: str
    status: str  # "pending", "in_progress", "completed", "error"
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class VideoAnalysis(BaseModel):
    id: Optional[str] = None
    url: str
    title: Optional[str] = None
    status: str = "pending"  # "pending", "processing", "completed", "error"
    steps: List[AnalysisStep] = []
    transcription: Optional[str] = None
    sentiment: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    user_id: Optional[str] = None
