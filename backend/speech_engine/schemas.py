"""Schemas for GyanDrishti Speech Engine.

Provides strongly typed Pydantic models for transcription segments,
language metadata, and raw lecture transcription results.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional
from pydantic import BaseModel, Field, field_validator


class TranscriptionSegment(BaseModel):
    """Represents a discrete timestamped speech segment from the ASR engine.

    Raw transcripts are source data. Spoken text and scripts are preserved
    exactly as spoken without auto-translation.
    """

    id: int = Field(..., description="Unique sequential identifier for the segment within the transcript")
    start: float = Field(..., description="Start timestamp in seconds from audio beginning")
    end: float = Field(..., description="End timestamp in seconds from audio beginning")
    text: str = Field(..., description="Transcribed spoken text preserving original language and script")
    language: List[str] = Field(
        default_factory=list,
        description="List of detected languages in this segment (e.g. ['en'], ['hi', 'en'], ['bn', 'en'])",
    )
    confidence: Optional[float] = Field(
        default=None,
        description="Model confidence score if reliably provided; null otherwise. Never fabricated.",
    )
    words: Optional[List[dict[str, Any]]] = Field(
        default=None,
        description="Optional word-level timestamps if supported and requested. No fake precision.",
    )

    @field_validator("start", "end", mode="after")
    @classmethod
    def round_timestamps(cls, v: float) -> float:
        return round(float(v), 2)


class TranscriptionResult(BaseModel):
    """Structured representation of a complete transcription session.

    Acts as the source data foundation for downstream lecture event extraction
    and Lecture Memory without modifying or overwriting original speech.
    """

    lecture_id: Optional[str] = Field(
        default=None,
        description="Optional lecture or session identifier",
    )
    audio_path: Optional[str] = Field(
        default=None,
        description="Local path to the source audio file if transcribed from file",
    )
    duration: float = Field(
        ...,
        description="Total duration of audio in seconds",
    )
    processing_time: float = Field(
        ...,
        description="Wall-clock time taken for transcription in seconds",
    )
    real_time_factor: float = Field(
        ...,
        description="Real-Time Factor (processing_time / duration). Lower is better.",
    )
    model_name: str = Field(
        ...,
        description="ASR model identifier (e.g. 'small', 'base')",
    )
    device: str = Field(
        ...,
        description="Inference device used (e.g. 'cpu', 'cuda')",
    )
    compute_type: str = Field(
        ...,
        description="Model precision / quantization (e.g. 'int8', 'float16')",
    )
    language_summary: List[str] = Field(
        default_factory=list,
        description="Aggregated list of all unique languages detected across all segments",
    )
    segments: List[TranscriptionSegment] = Field(
        default_factory=list,
        description="List of timestamped transcription segments",
    )
    raw_text: str = Field(
        ...,
        description="Concatenated transcript text from all segments",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of creation",
    )

    @field_validator("duration", "processing_time", "real_time_factor", mode="after")
    @classmethod
    def round_metrics(cls, v: float) -> float:
        return round(float(v), 4)

    def to_json(self, indent: int = 2) -> str:
        """Serializes the result to a formatted JSON string."""
        return self.model_dump_json(indent=indent)

    def save_json(self, file_path: str | Path) -> Path:
        """Saves the transcription result to a local JSON file."""
        target = Path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(self.to_json(indent=2))
        return target
