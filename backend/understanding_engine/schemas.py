"""Schemas for GyanDrishti Lecture Understanding Engine.

Defines strongly-typed Pydantic models for structured semantic understanding
extracted from multimodal synchronized lecture events.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class Concept(BaseModel):
    """Represents a core pedagogical concept discussed in a lecture block."""

    name: str = Field(..., description="Concise name of the concept (e.g. 'Ohm's Law', 'Electromagnetic Induction')")
    explanation: str = Field(..., description="Clear semantic explanation of the concept derived from the speech")
    timestamp_start: float = Field(..., description="Start timestamp in seconds where concept discussion begins")
    timestamp_end: float = Field(..., description="End timestamp in seconds where concept discussion ends")

    @field_validator("timestamp_start", "timestamp_end", mode="after")
    @classmethod
    def round_ts(cls, v: float) -> float:
        return round(float(v), 2)


class Definition(BaseModel):
    """Represents a formal or informal definition stated by the instructor."""

    term: str = Field(..., description="The term being defined")
    definition: str = Field(..., description="The explanation or definition provided by the teacher")
    timestamp: float = Field(..., description="Approximate timestamp in seconds where the definition was given")

    @field_validator("timestamp", mode="after")
    @classmethod
    def round_ts(cls, v: float) -> float:
        return round(float(v), 2)


class Equation(BaseModel):
    """Represents a mathematical or physical equation explicitly stated or dictated in speech."""

    latex_or_text: str = Field(..., description="Mathematical expression (e.g. 'I = V / R', 'EMF = - dPhi / dt')")
    description: str = Field(..., description="Brief description of the equation and its variables")
    timestamp: float = Field(..., description="Timestamp in seconds where the equation was stated")
    explicitly_spoken: bool = Field(
        default=True,
        description="Whether the equation was explicitly dictated by the speaker (avoids hallucination)",
    )
    grounding_status: str = Field(
        default="supported",
        description="Deterministic grounding status: 'supported', 'unsupported', 'uncertain'",
    )
    evidence_snippet: Optional[str] = Field(
        default=None,
        description="Source transcript snippet or token trace supporting this equation",
    )

    @field_validator("timestamp", mode="after")
    @classmethod
    def round_ts(cls, v: float) -> float:
        return round(float(v), 2)


class ImportantPoint(BaseModel):
    """Represents a high-salience takeaway, caution, or key insight highlighted by the instructor."""

    point: str = Field(..., description="The key takeaway statement")
    timestamp_start: float = Field(..., description="Start timestamp of the takeaway in seconds")
    timestamp_end: float = Field(..., description="End timestamp of the takeaway in seconds")
    importance: str = Field(default="high", description="Salience level: 'high', 'medium'")

    @field_validator("timestamp_start", "timestamp_end", mode="after")
    @classmethod
    def round_ts(cls, v: float) -> float:
        return round(float(v), 2)


class VisualReference(BaseModel):
    """Associates a visual keyframe or change event as contextual evidence for the understanding."""

    timestamp: float = Field(..., description="Timestamp of the visual event in seconds")
    source: str = Field(..., description="Origin source: 'camera', 'screen'")
    event_type: str = Field(default="keyframe", description="Type of visual event: 'keyframe', 'visual_change'")
    frame_path: Optional[str] = Field(default=None, description="Local filepath to the saved keyframe image")
    relevance: str = Field(..., description="Contextual explanation connecting visual evidence to spoken topic")

    @field_validator("timestamp", mode="after")
    @classmethod
    def round_ts(cls, v: float) -> float:
        return round(float(v), 2)


class QuestionCandidate(BaseModel):
    """Represents a potential revision or assessment question derived from the lecture block."""

    question: str = Field(..., description="The revision question")
    expected_answer: Optional[str] = Field(default=None, description="Expected answer based on lecture content")
    difficulty: str = Field(default="medium", description="Estimated difficulty: 'easy', 'medium', 'hard'")
    relevant_timestamp: float = Field(..., description="Timestamp of the supporting explanation in seconds")

    @field_validator("relevant_timestamp", mode="after")
    @classmethod
    def round_ts(cls, v: float) -> float:
        return round(float(v), 2)


class LectureUnderstanding(BaseModel):
    """Structured semantic understanding for a lecture segment or full multimodal block.

    Preserves source transcript references without modifying raw data.
    """

    lecture_id: Optional[str] = Field(default=None, description="Unique session or lecture identifier")
    time_start: float = Field(..., description="Start boundary of the understood lecture block in seconds")
    time_end: float = Field(..., description="End boundary of the understood lecture block in seconds")
    topic: str = Field(..., description="High-level topic or title of this lecture segment")
    concepts: List[Concept] = Field(default_factory=list, description="Extracted core concepts")
    definitions: List[Definition] = Field(default_factory=list, description="Extracted definitions")
    equations: List[Equation] = Field(default_factory=list, description="Explicitly supported equations")
    rejected_equations: List[Equation] = Field(
        default_factory=list,
        description="Equations proposed by LLM but rejected by deterministic grounding validator",
    )
    important_points: List[ImportantPoint] = Field(default_factory=list, description="High-salience key points")
    visual_references: List[VisualReference] = Field(
        default_factory=list,
        description="Associated visual evidence/keyframes",
    )
    question_candidates: List[QuestionCandidate] = Field(
        default_factory=list,
        description="Candidate revision/quiz questions",
    )
    confidence: float = Field(default=1.0, description="Overall extraction confidence score between 0.0 and 1.0")
    grounding_score: float = Field(
        default=1.0,
        description="Deterministic evidence grounding score computed from source verification",
    )
    raw_transcript_ref: Optional[str] = Field(
        default=None,
        description="Immutable reference copy of the raw source transcript text",
    )
    model_name: Optional[str] = Field(default=None, description="Identifier of the LLM model used for understanding")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of creation",
    )

    @field_validator("time_start", "time_end", mode="after")
    @classmethod
    def round_ts(cls, v: float) -> float:
        return round(float(v), 2)

    def to_json(self, indent: int = 2) -> str:
        """Serializes understanding to formatted JSON string."""
        return self.model_dump_json(indent=indent)

    def save_json(self, file_path: str | Path) -> Path:
        """Saves understanding to a JSON file."""
        target = Path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(self.to_json(indent=2))
        return target
