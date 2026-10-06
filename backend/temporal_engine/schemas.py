"""Schemas for GyanDrishti Temporal Fusion Engine.

Provides strongly-typed Pydantic models for speech events, visual events,
chronological timeline streams, and temporally synchronized multimodal blocks.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class SpeechEvent(BaseModel):
    """Represents a speech segment within the lecture timeline.

    Source transcript text is immutable source data and is preserved exactly as emitted.
    """

    start: float = Field(..., description="Start timestamp in seconds from lecture beginning")
    end: float = Field(..., description="End timestamp in seconds from lecture beginning")
    text: str = Field(..., description="Raw transcribed text from ASR engine, untouched")
    language: List[str] = Field(default_factory=list, description="Detected language codes (e.g. ['bn', 'en'])")
    script: Optional[List[str]] = Field(default=None, description="Detected writing scripts (e.g. ['Latin'])")
    confidence: Optional[float] = Field(default=None, description="Confidence score if present, never fabricated")
    words: Optional[List[Dict[str, Any]]] = Field(default=None, description="Word-level timestamps if available")

    @field_validator("start", "end", mode="after")
    @classmethod
    def round_timestamps(cls, v: float) -> float:
        return round(float(v), 2)


class VisualEvent(BaseModel):
    """Represents a visual event (board change, slide switch, or keyframe) from the video engine."""

    timestamp: float = Field(..., description="Timestamp in seconds relative to lecture start")
    source: str = Field(..., description="Visual source stream: 'camera', 'screen', etc.")
    type: str = Field(default="visual_change", description="Event category: 'visual_change', 'keyframe', etc.")
    change_score: float = Field(default=0.0, description="Pixel/motion difference score between 0.0 and 1.0")
    frame_path: str = Field(..., description="Path to the saved frame image on local disk")
    reason: str = Field(default="visual_change", description="Trigger reason (e.g. 'visual_change', 'manual')")
    raw_timestamp: Optional[float] = Field(default=None, description="Original epoch timestamp if normalized")

    @field_validator("timestamp", mode="after")
    @classmethod
    def round_timestamp(cls, v: float) -> float:
        return round(float(v), 2)


class TimelineEvent(BaseModel):
    """Atomic chronological event in the lecture stream."""

    timestamp: float = Field(..., description="Effective timestamp in seconds from lecture beginning")
    type: str = Field(..., description="Event type: 'speech', 'visual_change', 'keyframe', etc.")
    source: str = Field(..., description="Origin source: 'speech', 'camera', 'screen'")
    data: Dict[str, Any] = Field(..., description="Underlying event payload (SpeechEvent or VisualEvent dict)")

    @field_validator("timestamp", mode="after")
    @classmethod
    def round_timestamp(cls, v: float) -> float:
        return round(float(v), 2)


class SynchronizedEvent(BaseModel):
    """Associated cluster of speech segments and visual events falling within temporal proximity."""

    start: float = Field(..., description="Start boundary of the synchronized temporal window in seconds")
    end: float = Field(..., description="End boundary of the synchronized temporal window in seconds")
    speech: List[SpeechEvent] = Field(default_factory=list, description="Speech segments occurring in window")
    visual_events: List[VisualEvent] = Field(default_factory=list, description="Visual events associated with window")

    @field_validator("start", "end", mode="after")
    @classmethod
    def round_timestamps(cls, v: float) -> float:
        return round(float(v), 2)


class TemporalWindowConfig(BaseModel):
    """Configuration for temporal association window."""

    window_before: float = Field(default=5.0, description="Seconds before speech start to associate visual events")
    window_after: float = Field(default=5.0, description="Seconds after speech end to associate visual events")
    cluster_speech_gap: float = Field(
        default=2.0,
        description="Maximum silence gap in seconds between consecutive speech segments to cluster into one block",
    )


class LectureTimeline(BaseModel):
    """Unified multimodal chronological timeline of a lecture session.

    Integrates speech transcripts and visual keyframes into both a linear event stream
    and grouped temporal clusters.
    """

    lecture_id: Optional[str] = Field(default=None, description="Unique session or lecture identifier")
    duration: float = Field(default=0.0, description="Total lecture duration in seconds")
    chronological_stream: List[TimelineEvent] = Field(
        default_factory=list,
        description="Strictly sorted linear stream of all events across modalities",
    )
    synchronized_events: List[SynchronizedEvent] = Field(
        default_factory=list,
        description="Grouped associations of speech and visual events within temporal proximity",
    )
    total_speech_events: int = Field(default=0, description="Total count of speech segments")
    total_visual_events: int = Field(default=0, description="Total count of visual events/keyframes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary lecture session metadata")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of timeline creation",
    )

    def to_json(self, indent: int = 2) -> str:
        """Serializes the timeline to formatted JSON."""
        return self.model_dump_json(indent=indent)

    def save_json(self, file_path: str | Path) -> Path:
        """Saves the timeline to a JSON file."""
        target = Path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(self.to_json(indent=2))
        return target

    def get_events_in_range(self, start_sec: float, end_sec: float) -> List[TimelineEvent]:
        """Returns chronological events falling within [start_sec, end_sec]."""
        return [
            evt for evt in self.chronological_stream
            if start_sec <= evt.timestamp <= end_sec
        ]

    def get_keyframes(self) -> List[VisualEvent]:
        """Returns all visual keyframe events present across the synchronized timeline."""
        seen_paths = set()
        keyframes = []
        for sync in self.synchronized_events:
            for ve in sync.visual_events:
                if ve.frame_path not in seen_paths:
                    seen_paths.add(ve.frame_path)
                    keyframes.append(ve)
        return keyframes
