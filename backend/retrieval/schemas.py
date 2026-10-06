"""Pydantic schemas for semantic chunking and retrieval."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class ChunkType(str, Enum):
    """Semantic category of lecture memory chunk."""
    CONCEPT = "concept"
    DEFINITION = "definition"
    EQUATION = "equation"
    IMPORTANT_POINT = "important_point"
    QUESTION = "question"
    VISUAL_EXPLANATION = "visual_explanation"
    MULTIMODAL_EVENT = "multimodal_event"
    TIMELINE_BLOCK = "timeline_block"


class MemoryChunk(BaseModel):
    """Atomic retrieval unit extracted from canonical LectureMemory."""
    chunk_id: str = Field(..., description="Unique deterministic chunk identifier")
    lecture_id: str = Field(..., description="Canonical lecture ID")
    session_id: str = Field(..., description="Session identifier")
    chunk_type: ChunkType = Field(..., description="Semantic item type")
    source_item_id: str = Field(..., description="ID of source memory item")
    timestamp_start: float = Field(..., description="Start timestamp in seconds")
    timestamp_end: float = Field(..., description="End timestamp in seconds")
    text: str = Field(..., description="Searchable textual representation")
    source_type: str = Field(..., description="Origin modality: 'speech', 'visual', 'multimodal', 'derived'")
    grounding_status: str = Field(
        default="trusted",
        description="Grounding status: 'trusted', 'supported', 'uncertain', 'unsupported'"
    )
    provenance: Optional[Dict[str, Any]] = Field(default=None, description="Provenance dictionary")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Supplementary metadata")

    @field_validator("timestamp_start", "timestamp_end", mode="after")
    @classmethod
    def round_ts(cls, v: float) -> float:
        return round(float(v), 2)


class RetrievalFilter(BaseModel):
    """Query filters for constrained vector search."""
    session_id: Optional[str] = None
    source_type: Optional[str] = None
    chunk_type: Optional[ChunkType] = None
    only_trusted: bool = True
    min_score: float = 0.0


class RetrievalResult(BaseModel):
    """Ranked search result with semantic similarity score and provenance."""
    score: float = Field(..., description="Cosine similarity score in [0.0, 1.0]")
    chunk: MemoryChunk = Field(..., description="Retrieved memory chunk")

    @field_validator("score", mode="after")
    @classmethod
    def clamp_score(cls, v: float) -> float:
        return round(max(0.0, min(1.0, float(v))), 4)
