"""Provenance tracking module for GyanDrishti Lecture Memory Engine.

Ensures every derived concept, definition, equation, and point is strictly
traceable to source evidence (speech transcripts, visual events, or multimodal clusters).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class Provenance(BaseModel):
    """Immutable evidence trace connecting a lecture memory element to raw source events."""

    source_type: str = Field(
        ...,
        description="Origin modality: 'speech', 'visual', 'multimodal', or 'derived'",
    )
    timestamp_start: Optional[float] = Field(
        default=None,
        description="Start timestamp in seconds from lecture beginning",
    )
    timestamp_end: Optional[float] = Field(
        default=None,
        description="End timestamp in seconds from lecture beginning",
    )
    source_id: Optional[str] = Field(
        default=None,
        description="Source identifier (e.g. segment ID, frame_path, or session ID)",
    )
    evidence_snippet: Optional[str] = Field(
        default=None,
        description="Exact raw quote from transcript or factual description of visual event",
    )
    grounding_status: str = Field(
        default="supported",
        description="Grounding verification state: 'supported', 'unsupported', 'uncertain'",
    )
    confidence: Optional[float] = Field(
        default=None,
        description="Confidence score if objectively derived, null otherwise. Never fabricated.",
    )

    @field_validator("timestamp_start", "timestamp_end", mode="after")
    @classmethod
    def round_ts(cls, v: Optional[float]) -> Optional[float]:
        return round(float(v), 2) if v is not None else None

    @field_validator("source_type", mode="after")
    @classmethod
    def validate_source_type(cls, v: str) -> str:
        valid_types = {"speech", "visual", "multimodal", "derived"}
        if v.lower() not in valid_types:
            raise ValueError(f"Invalid source_type '{v}'. Must be one of {valid_types}")
        return v.lower()


def create_speech_provenance(
    start: float,
    end: float,
    text_snippet: str,
    source_id: Optional[str] = None,
    grounding_status: str = "supported",
) -> Provenance:
    """Creates a provenance trace for an item supported by speech."""
    return Provenance(
        source_type="speech",
        timestamp_start=start,
        timestamp_end=end,
        source_id=source_id,
        evidence_snippet=text_snippet.strip(),
        grounding_status=grounding_status,
    )


def create_visual_provenance(
    timestamp: float,
    frame_path: str,
    event_type: str = "keyframe",
    grounding_status: str = "supported",
) -> Provenance:
    """Creates a provenance trace for an item supported by visual keyframe/event."""
    return Provenance(
        source_type="visual",
        timestamp_start=timestamp,
        timestamp_end=timestamp,
        source_id=frame_path,
        evidence_snippet=f"Visual {event_type} at {timestamp:.2f}s (frame: {frame_path})",
        grounding_status=grounding_status,
    )


def create_multimodal_provenance(
    start: float,
    end: float,
    speech_snippet: str,
    frame_path: Optional[str] = None,
    grounding_status: str = "supported",
) -> Provenance:
    """Creates a provenance trace for an item supported jointly by speech and visual events."""
    snippet = speech_snippet.strip()
    if frame_path:
        snippet += f" [Associated frame: {frame_path}]"
    return Provenance(
        source_type="multimodal",
        timestamp_start=start,
        timestamp_end=end,
        source_id=frame_path,
        evidence_snippet=snippet,
        grounding_status=grounding_status,
    )


def create_derived_provenance(
    start: Optional[float] = None,
    end: Optional[float] = None,
    evidence_snippet: Optional[str] = None,
    grounding_status: str = "supported",
) -> Provenance:
    """Creates a provenance trace for higher-level structured items derived from trusted understanding."""
    return Provenance(
        source_type="derived",
        timestamp_start=start,
        timestamp_end=end,
        evidence_snippet=evidence_snippet,
        grounding_status=grounding_status,
    )
