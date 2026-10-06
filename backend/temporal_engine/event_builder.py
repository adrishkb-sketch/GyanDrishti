"""Event builder for GyanDrishti Temporal Engine.

Converts diverse ingestion payloads (Speech Transcripts, Video Manifests, raw dicts)
into standardized SpeechEvent, VisualEvent, and TimelineEvent domain models.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .schemas import SpeechEvent, TimelineEvent, VisualEvent


def _parse_iso_to_epoch(iso_str: str) -> Optional[float]:
    """Parses ISO timestamp string to epoch seconds."""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.timestamp()
    except Exception:
        return None


class EventBuilder:
    """Builds and normalizes events from speech and video engine outputs."""

    @staticmethod
    def build_speech_events(
        source_data: Union[Dict[str, Any], List[Any], str, Path],
    ) -> List[SpeechEvent]:
        """Parses speech transcript output into a list of SpeechEvent objects.

        Accepts:
            - Dict (e.g. TranscriptionResult dump)
            - List of segments (e.g. TranscriptionSegment instances or dicts)
            - File path to transcript JSON
        """
        if isinstance(source_data, (str, Path)):
            path = Path(source_data)
            if not path.is_file():
                raise FileNotFoundError(f"Speech transcript file not found: {path}")
            with open(path, "r", encoding="utf-8") as f:
                source_data = json.load(f)

        raw_segments: List[Any] = []
        if isinstance(source_data, dict):
            raw_segments = source_data.get("segments", [])
        elif isinstance(source_data, list):
            raw_segments = source_data
        else:
            return []

        events: List[SpeechEvent] = []
        for item in raw_segments:
            if hasattr(item, "model_dump"):
                d = item.model_dump()
            elif isinstance(item, dict):
                d = item
            else:
                continue

            events.append(
                SpeechEvent(
                    start=float(d.get("start", 0.0)),
                    end=float(d.get("end", 0.0)),
                    text=str(d.get("text", "")).strip(),
                    language=list(d.get("language", [])),
                    script=d.get("script"),
                    confidence=d.get("confidence"),
                    words=d.get("words"),
                )
            )

        # Deterministic sort by start timestamp
        return sorted(events, key=lambda s: (s.start, s.end, s.text))

    @staticmethod
    def build_visual_events(
        source_data: Union[Dict[str, Any], List[Any], str, Path],
        session_start_epoch: Optional[float] = None,
    ) -> List[VisualEvent]:
        """Parses video engine output or manifests into a list of VisualEvent objects.

        Handles both relative timestamps (e.g. 11.3s) and absolute Unix epoch timestamps
        (e.g. 1791296500.41s) by normalizing to relative lecture seconds when session start is known.
        """
        if isinstance(source_data, (str, Path)):
            path = Path(source_data)
            if not path.is_file():
                raise FileNotFoundError(f"Video manifest file not found: {path}")
            with open(path, "r", encoding="utf-8") as f:
                source_data = json.load(f)

        raw_events: List[Any] = []
        inferred_start_epoch = session_start_epoch

        if isinstance(source_data, dict):
            raw_events = source_data.get("events", [])
            # Try to infer session start from manifest metadata if not provided
            if inferred_start_epoch is None:
                start_time_val = source_data.get("start_time")
                if isinstance(start_time_val, str):
                    inferred_start_epoch = _parse_iso_to_epoch(start_time_val)
                elif isinstance(start_time_val, (int, float)):
                    inferred_start_epoch = float(start_time_val)
        elif isinstance(source_data, list):
            raw_events = source_data
        else:
            return []

        # If events have high absolute epoch values (> 1_000_000_000) and no start epoch was found,
        # infer start from the earliest event timestamp or first event
        first_ts = None
        for item in raw_events:
            ts = item.get("timestamp") if isinstance(item, dict) else getattr(item, "timestamp", None)
            if ts is not None and float(ts) > 1_000_000_000:
                first_ts = float(ts) if first_ts is None else min(first_ts, float(ts))

        if inferred_start_epoch is None and first_ts is not None:
            inferred_start_epoch = first_ts

        visual_events: List[VisualEvent] = []
        for item in raw_events:
            if hasattr(item, "model_dump"):
                d = item.model_dump()
            elif isinstance(item, dict):
                d = item
            else:
                continue

            raw_ts = float(d.get("timestamp", 0.0))
            # Determine relative timestamp
            if raw_ts > 1_000_000_000 and inferred_start_epoch is not None:
                rel_ts = max(0.0, raw_ts - inferred_start_epoch)
            else:
                rel_ts = raw_ts

            visual_events.append(
                VisualEvent(
                    timestamp=rel_ts,
                    source=str(d.get("source", "video")),
                    type=str(d.get("type", "visual_change")),
                    change_score=float(d.get("change_score", 0.0)),
                    frame_path=str(d.get("frame_path", "")),
                    reason=str(d.get("reason", "visual_change")),
                    raw_timestamp=raw_ts if raw_ts != rel_ts else None,
                )
            )

        # Deterministic sort by relative timestamp, then source, then frame_path
        return sorted(visual_events, key=lambda v: (v.timestamp, v.source, v.frame_path))

    @staticmethod
    def to_timeline_events(
        speech_events: List[SpeechEvent],
        visual_events: List[VisualEvent],
    ) -> List[TimelineEvent]:
        """Merges speech and visual events into a strictly chronological stream of TimelineEvent objects.

        Sorting is completely deterministic:
        1. timestamp
        2. type ('speech' precedes visual events on exact timestamp matches)
        3. source ('camera', 'screen', etc.)
        """
        stream: List[TimelineEvent] = []

        for se in speech_events:
            stream.append(
                TimelineEvent(
                    timestamp=se.start,
                    type="speech",
                    source="speech",
                    data=se.model_dump(),
                )
            )

        for ve in visual_events:
            stream.append(
                TimelineEvent(
                    timestamp=ve.timestamp,
                    type=ve.type,
                    source=ve.source,
                    data=ve.model_dump(),
                )
            )

        # Deterministic sorting
        # Order: timestamp ascending; if tie: 'speech' before visual events; then source
        def sort_key(te: TimelineEvent):
            type_prio = 0 if te.type == "speech" else 1
            return (te.timestamp, type_prio, te.source)

        return sorted(stream, key=sort_key)
