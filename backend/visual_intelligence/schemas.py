"""Pydantic schemas for GyanDrishti Visual Intelligence Engine.

Provides strongly-typed schemas for OCR extractions, bounding boxes,
potential mathematical text detection, and multimodal associations.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class OCRStatus(str, Enum):
    """Execution status for OCR analysis of a keyframe."""
    SUCCESS = "success"
    NO_TEXT_DETECTED = "no_text_detected"
    UNCERTAIN = "uncertain"
    FAILED = "failed"
    IMAGE_NOT_FOUND = "image_not_found"


class PreprocessingVariant(str, Enum):
    """Preprocessing pipelines evaluated on keyframes."""
    ORIGINAL = "original"
    GRAYSCALE = "grayscale"
    CLAHE = "clahe"
    ADAPTIVE_THRESHOLD = "adaptive_threshold"
    INVERTED_BLACKBOARD = "inverted_blackboard"


class BoundingBox(BaseModel):
    """Spatial bounding box for detected text region on a keyframe."""
    polygon: List[List[float]] = Field(
        ...,
        description="Four-point polygon coordinates [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]"
    )
    x_min: float = Field(..., description="Minimum x coordinate in pixels")
    y_min: float = Field(..., description="Minimum y coordinate in pixels")
    x_max: float = Field(..., description="Maximum x coordinate in pixels")
    y_max: float = Field(..., description="Maximum y coordinate in pixels")

    @classmethod
    def from_polygon(cls, polygon: List[List[float]]) -> BoundingBox:
        """Computes bounding rect from polygon points."""
        xs = [pt[0] for pt in polygon]
        ys = [pt[1] for pt in polygon]
        return cls(
            polygon=polygon,
            x_min=round(float(min(xs)), 1),
            y_min=round(float(min(ys)), 1),
            x_max=round(float(max(xs)), 1),
            y_max=round(float(max(ys)), 1),
        )


class VisualTextEvidence(BaseModel):
    """Atomic text unit recognized on a keyframe with confidence and spatial coordinates."""
    id: str = Field(..., description="Unique evidence identifier")
    session_id: Optional[str] = Field(default=None, description="Associated lecture session identifier")
    keyframe_id: str = Field(..., description="Identifier of the keyframe frame image")
    timestamp: float = Field(..., description="Timestamp in seconds from lecture beginning")
    text: str = Field(..., description="Unmodified extracted text from OCR")
    confidence: float = Field(..., description="OCR recognition confidence score bounded in [0.0, 1.0]")
    bounding_box: Optional[BoundingBox] = Field(default=None, description="Spatial coordinates if detected")
    language: Optional[str] = Field(default=None, description="Detected script/language if available")
    preprocessing_variant: str = Field(
        default="original",
        description="Name of the preprocessing filter yielding this detection"
    )
    source_image: str = Field(..., description="Filepath or URI to the keyframe image on disk")
    is_potential_math: bool = Field(
        default=False,
        description="True if string contains equations, mathematical symbols, or formula patterns"
    )

    @field_validator("confidence", mode="after")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        """Ensures confidence remains strictly bounded in [0.0, 1.0]."""
        val = float(v)
        return round(max(0.0, min(1.0, val)), 4)

    @field_validator("timestamp", mode="after")
    @classmethod
    def round_timestamp(cls, v: float) -> float:
        return round(float(v), 2)


class VisualAnalysisResult(BaseModel):
    """Comprehensive visual intelligence output for a single keyframe."""
    keyframe_id: str = Field(..., description="Keyframe identifier")
    timestamp: float = Field(..., description="Keyframe timestamp in seconds")
    source_image: str = Field(..., description="Local filepath to the analysed frame")
    extracted_text: List[VisualTextEvidence] = Field(
        default_factory=list,
        description="List of detected text lines / snippets"
    )
    raw_text_combined: str = Field(
        default="",
        description="Whitespace-joined concatenation of all recognized text lines"
    )
    overall_confidence: float = Field(
        default=0.0,
        description="Mean confidence across extracted text items, or 0.0 if empty"
    )
    processing_status: OCRStatus = Field(
        default=OCRStatus.SUCCESS,
        description="Status code for this analysis operation"
    )
    potential_equations: List[str] = Field(
        default_factory=list,
        description="Sub-strings matching mathematical equations or expressions"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Diagnostic notes or warnings encountered during processing"
    )
    latency_ms: float = Field(
        default=0.0,
        description="Processing latency for preprocessing + OCR in milliseconds"
    )
    image_dimensions: Optional[Dict[str, int]] = Field(
        default=None,
        description="Width and height of the analysed frame"
    )

    @field_validator("overall_confidence", mode="after")
    @classmethod
    def clamp_overall_confidence(cls, v: float) -> float:
        val = float(v)
        return round(max(0.0, min(1.0, val)), 4)


class MultimodalAssociation(BaseModel):
    """Temporal linkage between spoken evidence and visual text evidence."""
    id: str = Field(..., description="Unique association identifier")
    session_id: Optional[str] = Field(default=None, description="Lecture session ID")
    speech_segment_id: Optional[str] = Field(default=None, description="Spoken transcript segment ID")
    speech_text: Optional[str] = Field(default=None, description="Spoken transcript text")
    speech_timestamp_start: Optional[float] = Field(default=None, description="Start timestamp of speech")
    speech_timestamp_end: Optional[float] = Field(default=None, description="End timestamp of speech")
    visual_keyframe_id: Optional[str] = Field(default=None, description="Keyframe ID of visual evidence")
    visual_timestamp: Optional[float] = Field(default=None, description="Timestamp of visual keyframe")
    visual_extracted_text: Optional[str] = Field(default=None, description="Text recognized on keyframe")
    temporal_offset_seconds: Optional[float] = Field(
        default=None,
        description="Delta between visual timestamp and speech midpoint in seconds"
    )
    association_type: str = Field(
        default="multimodal_grounded",
        description="Category: 'multimodal_grounded' | 'speech_only' | 'visual_only'"
    )
    confidence: float = Field(
        default=0.0,
        description="Joint multimodal confidence score in [0.0, 1.0]"
    )
