from pydantic import BaseModel
from typing import Optional, List

class FrameMetadata(BaseModel):
    source: str
    frame_id: int
    timestamp: float
    width: int
    height: int

class Event(BaseModel):
    timestamp: float
    source: str
    type: str
    change_score: float
    frame_path: str
    reason: str

class Manifest(BaseModel):
    session_id: str
    start_time: str
    sources: List[str]
    recordings: dict[str, str]
    events: List[Event]
