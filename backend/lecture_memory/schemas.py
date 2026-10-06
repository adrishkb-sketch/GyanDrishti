"""Schemas for GyanDrishti Canonical Lecture Memory (Milestone 5).

Defines strongly-typed Pydantic models for persistent, evidence-grounded lecture memory
with strict provenance, local persistence guarantees, and UI compatibility.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from .provenance import Provenance, create_derived_provenance


class MemoryConcept(BaseModel):
    """Core pedagogical concept stored in lecture memory."""

    id: str = Field(..., description="Unique concept identifier within the lecture (e.g. 'c1', 'c2')")
    name: str = Field(..., description="Concept title or formal name")
    explanation: str = Field(..., description="Detailed semantic explanation grounded in teacher explanation")
    timestamp: float = Field(..., description="Representative timestamp in seconds for fast UI seek")
    timestamp_start: float = Field(..., description="Start timestamp of concept discussion in seconds")
    timestamp_end: float = Field(..., description="End timestamp of concept discussion in seconds")
    provenance: Provenance = Field(..., description="Evidence provenance connecting concept to source events")

    @field_validator("timestamp", "timestamp_start", "timestamp_end", mode="after")
    @classmethod
    def round_ts(cls, v: float) -> float:
        return round(float(v), 2)


class MemoryDefinition(BaseModel):
    """Formal or informal definition stated by instructor."""

    term: str = Field(..., description="The term being defined")
    definition: str = Field(..., description="The explanation or definition given by the teacher")
    timestamp: float = Field(..., description="Timestamp in seconds where the definition occurred")
    provenance: Provenance = Field(..., description="Evidence provenance connecting definition to source events")

    @field_validator("timestamp", mode="after")
    @classmethod
    def round_ts(cls, v: float) -> float:
        return round(float(v), 2)


class MemoryEquation(BaseModel):
    """Mathematical or physical equation strictly supported by multimodal evidence."""

    name: str = Field(..., description="Formula or law name (e.g. 'Ohm\\'s Law', 'Faraday\\'s Law')")
    representation: str = Field(..., description="LaTeX or mathematical expression (e.g. 'I = V / R')")
    explanation: str = Field(..., description="Explanation of formula variables and physical meaning")
    timestamp: float = Field(..., description="Timestamp in seconds where equation was stated")
    grounding_status: str = Field(
        default="supported",
        description="Grounding status: 'supported', 'unsupported', 'uncertain'",
    )
    evidence_snippet: Optional[str] = Field(
        default=None,
        description="Transcript snippet or token trace directly supporting the equation",
    )
    provenance: Provenance = Field(..., description="Evidence provenance trace")

    @field_validator("timestamp", mode="after")
    @classmethod
    def round_ts(cls, v: float) -> float:
        return round(float(v), 2)


class MemoryImportantPoint(BaseModel):
    """High-salience pedagogical takeaway or instructor emphasis."""

    point: str = Field(..., description="The key takeaway statement")
    timestamp: float = Field(..., description="Representative timestamp in seconds for fast UI seek")
    importance: str = Field(default="high", description="Salience level: 'high', 'medium', 'uncertain'")
    provenance: Provenance = Field(..., description="Evidence provenance trace")

    @field_validator("timestamp", mode="after")
    @classmethod
    def round_ts(cls, v: float) -> float:
        return round(float(v), 2)


class MemoryVisualReference(BaseModel):
    """Contextual visual evidence (keyframe or board event) without fabricated contents."""

    timestamp: float = Field(..., description="Timestamp of the visual event in seconds")
    source: str = Field(..., description="Visual stream origin: 'Camera', 'Screen', etc.")
    event_type: str = Field(..., description="Visual event type: 'Keyframe', 'Board Writing', 'Slide Change'")
    local_frame_reference: str = Field(
        ...,
        description="Local disk frame path or descriptive visual reference",
    )
    description: Optional[str] = Field(
        default=None,
        description="Contextual explanation connecting visual event to spoken context",
    )
    keyframe_id: Optional[str] = Field(default=None, description="Identifier of the keyframe")
    event_id: Optional[str] = Field(default=None, description="Visual event identifier")
    extracted_text: Optional[str] = Field(
        default=None,
        description="Text recognized by local OCR on keyframe",
    )
    ocr_confidence: Optional[float] = Field(
        default=None,
        description="Confidence of visual OCR recognition bounded in [0.0, 1.0]",
    )
    ocr_status: str = Field(
        default="ocr_pending",
        description="OCR status: 'ocr_pending', 'success', 'no_text_detected', 'uncertain', 'failed'",
    )
    potential_equations: List[str] = Field(
        default_factory=list,
        description="Candidate equations identified in visual text",
    )
    provenance: Provenance = Field(..., description="Evidence provenance trace")

    @field_validator("timestamp", mode="after")
    @classmethod
    def round_ts(cls, v: float) -> float:
        return round(float(v), 2)

    @field_validator("ocr_confidence", mode="after")
    @classmethod
    def clamp_ocr_confidence(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return None
        return round(max(0.0, min(1.0, float(v))), 4)


class MemoryQuestionCandidate(BaseModel):
    """Candidate assessment or revision question derived from trusted lecture understanding."""

    question: str = Field(..., description="Revision question text")
    answer: str = Field(..., description="Expected answer grounded in lecture explanation")
    difficulty: str = Field(default="medium", description="Difficulty level: 'easy', 'medium', 'hard'")
    timestamp: float = Field(..., description="Timestamp in seconds for review navigation")
    provenance: Provenance = Field(..., description="Evidence provenance trace")

    @field_validator("timestamp", mode="after")
    @classmethod
    def round_ts(cls, v: float) -> float:
        return round(float(v), 2)


class MemoryTimelineEvent(BaseModel):
    """Unified chronological timeline event for player navigation and linear lecture playback."""

    timestamp: float = Field(..., description="Timestamp in seconds from lecture start")
    type: str = Field(
        ...,
        description="Category: 'speech' | 'visual' | 'keyframe' | 'equation' | 'concept' | 'multimodal'",
    )
    label: str = Field(..., description="Concise display label (e.g. 'Important concept', 'Equation stated')")
    details: Optional[str] = Field(default=None, description="Detailed snippet or description")
    provenance: Optional[Provenance] = Field(default=None, description="Supporting evidence trace")

    @field_validator("timestamp", mode="after")
    @classmethod
    def round_ts(cls, v: float) -> float:
        return round(float(v), 2)


class LectureMetadata(BaseModel):
    """Session-level ingestion and language metadata."""

    subject: str = Field(default="General Lecture", description="Academic subject or domain")
    instructor: Optional[str] = Field(default=None, description="Instructor name if cautiously verified")
    language_summary: List[str] = Field(default_factory=list, description="Languages detected (e.g. ['bn', 'en'])")
    scripts_summary: List[str] = Field(default_factory=list, description="Scripts detected (e.g. ['Latin', 'Bengali'])")
    total_speech_segments: int = Field(default=0, description="Total speech segments ingested")
    total_visual_events: int = Field(default=0, description="Total visual keyframes ingested")
    source_recordings: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of stream source to relative recording filepath",
    )


class LectureMemory(BaseModel):
    """Canonical persistent memory representation of a completed lecture session.

    Integrates temporal streams, grounded understanding, visual keyframe references,
    and rigorous evidence provenance. Never contains unverified hallucinations.
    """

    schema_version: str = Field(default="1.0.0", description="Lecture memory schema specification version")
    session_id: str = Field(..., description="Unique session or lecture identifier")
    title: str = Field(..., description="Formal lecture title derived from grounded understanding")
    subject: str = Field(default="General Lecture", description="Subject or course name")
    date: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%B %d, %Y"),
        description="Human-readable lecture date",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC creation timestamp",
    )
    duration: float = Field(default=0.0, description="Total lecture duration in seconds")
    storage_local: bool = Field(default=True, description="Always True for offline-first local storage")
    overview: str = Field(..., description="Synthesized pedagogical overview grounded in verified concepts")

    timeline_events: List[MemoryTimelineEvent] = Field(
        default_factory=list,
        description="Chronological event stream for UI timeline and player seeking",
    )
    concepts: List[MemoryConcept] = Field(
        default_factory=list,
        description="Grounded core pedagogical concepts",
    )
    definitions: List[MemoryDefinition] = Field(
        default_factory=list,
        description="Grounded formal and informal definitions",
    )
    equations: List[MemoryEquation] = Field(
        default_factory=list,
        description="TRUSTED ONLY: Equations verified by deterministic evidence grounding",
    )
    rejected_equations: List[MemoryEquation] = Field(
        default_factory=list,
        description="AUDIT ONLY: Hallucinated equations rejected by deterministic grounding validator",
    )
    important_points: List[MemoryImportantPoint] = Field(
        default_factory=list,
        description="High-salience takeaways and instructor emphases",
    )
    visual_references: List[MemoryVisualReference] = Field(
        default_factory=list,
        description="Visual keyframe events without fabricated contents",
    )
    revision_questions: List[MemoryQuestionCandidate] = Field(
        default_factory=list,
        description="Candidate revision and self-assessment questions",
    )
    metadata: LectureMetadata = Field(
        default_factory=LectureMetadata,
        description="Ingestion session and language metadata",
    )
    grounding_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Objective evidence validation metrics (grounding score, items checked, items rejected)",
    )

    @field_validator("duration", mode="after")
    @classmethod
    def round_duration(cls, v: float) -> float:
        return round(float(v), 2)

    def to_json(self, indent: int = 2) -> str:
        """Serializes the canonical lecture memory to formatted JSON string."""
        return self.model_dump_json(indent=indent)

    def save_json(self, file_path: str | Path) -> Path:
        """Saves lecture memory to JSON file."""
        target = Path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(self.to_json(indent=2))
        return target

    @classmethod
    def from_json(cls, json_str: str) -> LectureMemory:
        """Parses a JSON string into a strongly-typed LectureMemory instance."""
        return cls.model_validate_json(json_str)

    def to_frontend_dict(self) -> Dict[str, Any]:
        """Exports data into the exact shape consumed by the frontend LectureViewer component."""
        return {
            "session_id": self.session_id,
            "title": self.title,
            "subject": self.subject,
            "date": self.date,
            "duration": int(self.duration),
            "storage_local": self.storage_local,
            "overview": self.overview,
            "timeline_events": [
                {
                    "timestamp": round(evt.timestamp, 1),
                    "type": evt.type,
                    "label": evt.label,
                    "details": evt.details,
                }
                for evt in self.timeline_events
            ],
            "concepts": [
                {
                    "id": c.id,
                    "name": c.name,
                    "explanation": c.explanation,
                    "timestamp": round(c.timestamp, 1),
                }
                for c in self.concepts
            ],
            "definitions": [
                {
                    "term": d.term,
                    "definition": d.definition,
                    "timestamp": round(d.timestamp, 1),
                }
                for d in self.definitions
            ],
            "equations": [
                {
                    "name": eq.name,
                    "representation": eq.representation,
                    "explanation": eq.explanation,
                    "timestamp": round(eq.timestamp, 1),
                }
                for eq in self.equations
            ],
            "important_points": [
                {
                    "point": pt.point,
                    "timestamp": round(pt.timestamp, 1),
                }
                for pt in self.important_points
            ],
            "visual_references": [
                {
                    "timestamp": round(vr.timestamp, 1),
                    "source": vr.source,
                    "event_type": vr.event_type,
                    "local_frame_reference": vr.local_frame_reference,
                    "description": vr.description,
                    "keyframe_id": vr.keyframe_id,
                    "extracted_text": vr.extracted_text,
                    "ocr_confidence": round(vr.ocr_confidence, 2) if vr.ocr_confidence is not None else None,
                    "ocr_status": vr.ocr_status,
                    "potential_equations": vr.potential_equations,
                }
                for vr in self.visual_references
            ],
            "revision_questions": [
                {
                    "question": q.question,
                    "answer": q.answer,
                    "timestamp": round(q.timestamp, 1),
                }
                for q in self.revision_questions
            ],
        }
