"""Pydantic schemas for Visual Reasoning and Diagram Understanding."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class DiagramType(str, Enum):
    """Categorization of visual diagram content."""
    CIRCUIT_DIAGRAM = "circuit_diagram"
    GRAPH_PLOT = "graph_plot"
    GEOMETRIC_DIAGRAM = "geometric_diagram"
    FLOWCHART_BLOCK = "flowchart_block"
    EQUATION_LAYOUT = "equation_layout"
    TABLE = "table"
    GENERIC_DIAGRAM = "generic_diagram"
    NO_DIAGRAM = "no_diagram"


class VLMValidationStatus(str, Enum):
    """Evidence grounding status of the visual understanding proposal."""
    PROPOSED = "proposed"
    VALIDATED = "validated"
    OCR_CONFLICT = "ocr_conflict"
    UNCERTAIN = "uncertain"
    REJECTED = "rejected"
    EMPTY_IMAGE = "empty_image"


class VisualReasoningProposal(BaseModel):
    """Raw structured proposal emitted by the local VLM."""
    model_name: str = Field(..., description="VLM model identifier (e.g. 'qwen2-vl:2b', 'minicpm-v')")
    model_version: Optional[str] = Field(default=None, description="Model revision or quantization")
    diagram_type: DiagramType = Field(default=DiagramType.GENERIC_DIAGRAM)
    description: str = Field(..., description="High-level description of diagram structures")
    entities_detected: List[str] = Field(
        default_factory=list,
        description="Identified components (e.g. ['Resistor R1', 'Battery V1', 'Ammeter'])"
    )
    relations_detected: List[str] = Field(
        default_factory=list,
        description="Identified topological relations (e.g. ['R1 connected in series with V1'])"
    )
    visible_equations: List[str] = Field(
        default_factory=list,
        description="Any mathematical formulas observed in diagram annotations"
    )
    confidence: float = Field(
        default=0.8,
        description="Self-reported model confidence bounded in [0.0, 1.0]"
    )
    raw_response: str = Field(default="", description="Original raw JSON/text output from provider")

    @field_validator("confidence", mode="after")
    @classmethod
    def clamp_conf(cls, v: float) -> float:
        return round(max(0.0, min(1.0, float(v))), 4)


class VisualReasoningResult(BaseModel):
    """Audited, evidence-grounded visual reasoning record."""
    id: str = Field(..., description="Unique reasoning result identifier")
    session_id: Optional[str] = Field(default=None, description="Lecture session ID")
    keyframe_id: str = Field(..., description="Keyframe ID of analyzed frame")
    timestamp: float = Field(..., description="Timestamp in seconds from lecture start")
    frame_path: str = Field(..., description="Local filepath to keyframe image")
    raw_ocr_text: Optional[str] = Field(
        default=None,
        description="Raw immutable OCR evidence for verification"
    )
    proposal: Optional[VisualReasoningProposal] = Field(
        default=None,
        description="VLM understanding proposal if inference succeeded"
    )
    validation_status: VLMValidationStatus = Field(
        default=VLMValidationStatus.PROPOSED,
        description="Deterministic validation outcome"
    )
    conflict_notes: Optional[str] = Field(
        default=None,
        description="Detailed mismatch notes if OCR and VLM disagree"
    )
    provenance_source: str = Field(
        default="visual_vlm",
        description="Modality indicator distinguishing visual VLM proposals from spoken facts"
    )
    latency_ms: float = Field(default=0.0, description="Inference latency in milliseconds")

    @field_validator("timestamp", mode="after")
    @classmethod
    def round_ts(cls, v: float) -> float:
        return round(float(v), 2)
