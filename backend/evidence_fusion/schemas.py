"""Schemas for GyanDrishti Multimodal Evidence Fusion Engine.

Defines state machines, source representations, and fused multimodal evidence records.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class FusionState(str, Enum):
    """Possible semantic fusion states between speech and visual evidence."""
    SPEECH_ONLY = "speech_only"
    VISUAL_ONLY = "visual_only"
    MULTIMODAL_SUPPORTED = "multimodal_supported"
    CONFLICT = "conflict"
    UNCERTAIN = "uncertain"
    UNSUPPORTED = "unsupported"


class EvidenceSourceType(str, Enum):
    """Origin modality for evidence provenance."""
    SPEECH = "speech"
    VISUAL = "visual"
    MULTIMODAL = "multimodal"
    DERIVED = "derived"


class SpeechEvidenceItem(BaseModel):
    """Discrete speech segment evidence with timestamp bounds."""
    speech_id: str = Field(..., description="Unique speech segment identifier")
    timestamp_start: float = Field(..., description="Start timestamp in seconds")
    timestamp_end: float = Field(..., description="End timestamp in seconds")
    text: str = Field(..., description="Raw untouched transcription text")
    confidence: Optional[float] = Field(default=None, description="ASR confidence if available")
    detected_math: Optional[str] = Field(default=None, description="Normalized spoken equation if any")

    @field_validator("timestamp_start", "timestamp_end", mode="after")
    @classmethod
    def round_ts(cls, v: float) -> float:
        return round(float(v), 2)


class VisualEvidenceItem(BaseModel):
    """Visual keyframe OCR evidence."""
    keyframe_id: str = Field(..., description="Keyframe identifier")
    timestamp: float = Field(..., description="Keyframe timestamp in seconds")
    frame_path: str = Field(..., description="Local filepath to keyframe image")
    raw_text: str = Field(..., description="Extracted OCR text string")
    confidence: float = Field(..., description="OCR recognition confidence in [0.0, 1.0]")
    potential_equations: List[str] = Field(default_factory=list, description="Candidate formulas detected")

    @field_validator("confidence", mode="after")
    @classmethod
    def clamp_conf(cls, v: float) -> float:
        return round(max(0.0, min(1.0, float(v))), 4)

    @field_validator("timestamp", mode="after")
    @classmethod
    def round_ts(cls, v: float) -> float:
        return round(float(v), 2)


class FusedEvidenceItem(BaseModel):
    """Consolidated multimodal evidence unit with deterministic audit trail."""
    id: str = Field(..., description="Unique fusion record ID")
    session_id: Optional[str] = Field(default=None, description="Lecture session ID")
    state: FusionState = Field(..., description="Deterministic fusion classification")
    primary_concept: str = Field(..., description="Salient topic, formula, or law referenced")
    canonical_representation: Optional[str] = Field(
        default=None,
        description="Standardized formula or phrase (e.g. 'I = V / R')"
    )
    speech_evidence: Optional[SpeechEvidenceItem] = Field(
        default=None,
        description="Linked speech evidence item if present"
    )
    visual_evidence: Optional[VisualEvidenceItem] = Field(
        default=None,
        description="Linked visual OCR evidence item if present"
    )
    temporal_delta: Optional[float] = Field(
        default=None,
        description="Time offset in seconds between speech midpoint and visual keyframe"
    )
    fusion_confidence: float = Field(
        ...,
        description="Calculated composite confidence score in [0.0, 1.0]"
    )
    conflict_details: Optional[str] = Field(
        default=None,
        description="Description of mathematical or conceptual mismatch if state is conflict"
    )
    notes: str = Field(default="", description="Audit reason or policy decision explanation")

    @field_validator("fusion_confidence", mode="after")
    @classmethod
    def clamp_conf(cls, v: float) -> float:
        return round(max(0.0, min(1.0, float(v))), 4)


class MultimodalFusionReport(BaseModel):
    """Aggregate summary of multimodal evidence fusion for a lecture session."""
    session_id: str = Field(..., description="Lecture session ID")
    total_speech_segments: int = Field(default=0)
    total_visual_keyframes: int = Field(default=0)
    fused_items: List[FusedEvidenceItem] = Field(default_factory=list)
    multimodal_supported_count: int = Field(default=0)
    visual_only_count: int = Field(default=0)
    speech_only_count: int = Field(default=0)
    conflict_count: int = Field(default=0)
    uncertain_count: int = Field(default=0)
    unsupported_count: int = Field(default=0)
