"""Timeline construction module for GyanDrishti Temporal Engine.

Orchestrates speech normalization, visual event alignment, linear chronological streaming,
and grouped multimodal block synchronization into a unified LectureTimeline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .event_builder import EventBuilder
from .schemas import (
    LectureTimeline,
    SpeechEvent,
    SynchronizedEvent,
    TemporalWindowConfig,
    TimelineEvent,
    VisualEvent,
)
from .synchronizer import TemporalSynchronizer


class TimelineBuilder:
    """Constructs deterministic, unified lecture timelines from multimodal inputs."""

    def __init__(
        self,
        config: Optional[TemporalWindowConfig] = None,
        window_before: Optional[float] = None,
        window_after: Optional[float] = None,
    ) -> None:
        self.config = config or TemporalWindowConfig()
        if window_before is not None:
            self.config.window_before = float(window_before)
        if window_after is not None:
            self.config.window_after = float(window_after)
        self.synchronizer = TemporalSynchronizer(config=self.config)

    def build_timeline(
        self,
        speech_source: Optional[Union[Dict[str, Any], List[Any], str, Path]] = None,
        visual_source: Optional[Union[Dict[str, Any], List[Any], str, Path]] = None,
        lecture_id: Optional[str] = None,
        session_start_epoch: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LectureTimeline:
        """Assembles a unified LectureTimeline from speech and visual sources.

        Args:
            speech_source: Transcript JSON path, dict, or list of speech segments.
            visual_source: Manifest JSON path, dict, or list of visual events.
            lecture_id: Optional session identifier.
            session_start_epoch: Optional start epoch timestamp for relative normalization.
            metadata: Optional arbitrary session metadata.

        Returns:
            Deterministic LectureTimeline object.
        """
        # 1. Build and normalize speech events
        speech_events: List[SpeechEvent] = []
        if speech_source is not None:
            speech_events = EventBuilder.build_speech_events(speech_source)

        # 2. Build and normalize visual events
        visual_events: List[VisualEvent] = []
        if visual_source is not None:
            visual_events = EventBuilder.build_visual_events(
                visual_source,
                session_start_epoch=session_start_epoch,
            )

        # 3. Build linear chronological event stream
        chronological_stream: List[TimelineEvent] = EventBuilder.to_timeline_events(
            speech_events=speech_events,
            visual_events=visual_events,
        )

        # 4. Perform temporal window association
        synchronized_events: List[SynchronizedEvent] = self.synchronizer.synchronize(
            speech_events=speech_events,
            visual_events=visual_events,
        )

        # 5. Compute overall timeline duration
        max_ts = 0.0
        if speech_events:
            max_ts = max(max_ts, max(s.end for s in speech_events))
        if visual_events:
            max_ts = max(max_ts, max(v.timestamp for v in visual_events))

        # Infer lecture_id if not explicitly provided
        inferred_id = lecture_id
        if inferred_id is None and isinstance(visual_source, dict):
            inferred_id = visual_source.get("session_id")
        if inferred_id is None and isinstance(speech_source, dict):
            inferred_id = speech_source.get("lecture_id")

        return LectureTimeline(
            lecture_id=inferred_id,
            duration=round(max_ts, 2),
            chronological_stream=chronological_stream,
            synchronized_events=synchronized_events,
            total_speech_events=len(speech_events),
            total_visual_events=len(visual_events),
            metadata=metadata or {},
        )


def create_lecture_timeline(
    speech_source: Optional[Union[Dict[str, Any], List[Any], str, Path]] = None,
    visual_source: Optional[Union[Dict[str, Any], List[Any], str, Path]] = None,
    lecture_id: Optional[str] = None,
    window_before: float = 5.0,
    window_after: float = 5.0,
    metadata: Optional[Dict[str, Any]] = None,
) -> LectureTimeline:
    """Convenience function to build a unified LectureTimeline in a single call."""
    builder = TimelineBuilder(window_before=window_before, window_after=window_after)
    return builder.build_timeline(
        speech_source=speech_source,
        visual_source=visual_source,
        lecture_id=lecture_id,
        metadata=metadata,
    )
