"""Unit tests for EventBuilder in Temporal Engine."""

import pytest
from temporal_engine.event_builder import EventBuilder
from temporal_engine.schemas import SpeechEvent, VisualEvent, TimelineEvent


def test_build_speech_events_preserves_raw_text() -> None:
    raw_text = "এখানে আমরা basically দেখছি যে current টা increase করছে।"
    source_payload = {
        "segments": [
            {
                "id": 1,
                "start": 10.254,
                "end": 14.891,
                "text": raw_text,
                "language": ["bn", "en"],
                "script": ["Bengali", "Latin"],
            }
        ]
    }
    events = EventBuilder.build_speech_events(source_payload)
    assert len(events) == 1
    se = events[0]
    assert se.start == 10.25
    assert se.end == 14.89
    assert se.text == raw_text  # Strictly preserved source text
    assert se.language == ["bn", "en"]
    assert se.script == ["Bengali", "Latin"]


def test_build_speech_events_empty_input() -> None:
    assert EventBuilder.build_speech_events([]) == []
    assert EventBuilder.build_speech_events({}) == []


def test_build_visual_events_relative_timestamps() -> None:
    payload = [
        {"timestamp": 5.4, "source": "camera", "type": "keyframe", "frame_path": "/tmp/cam.jpg"},
        {"timestamp": 8.1, "source": "screen", "type": "visual_change", "frame_path": "/tmp/scr.jpg"},
    ]
    events = EventBuilder.build_visual_events(payload)
    assert len(events) == 2
    assert events[0].timestamp == 5.4
    assert events[0].source == "camera"
    assert events[1].timestamp == 8.1
    assert events[1].source == "screen"


def test_build_visual_events_epoch_normalization() -> None:
    # Manifest with epoch timestamp and start_time
    manifest = {
        "session_id": "test_session",
        "start_time": "2026-10-06T12:00:00+00:00",  # epoch 1791288000.0
        "events": [
            {
                "timestamp": 1791288005.5,  # 5.5s after start
                "source": "camera",
                "type": "keyframe",
                "change_score": 0.45,
                "frame_path": "/tmp/f1.jpg",
            }
        ]
    }
    events = EventBuilder.build_visual_events(manifest, session_start_epoch=1791288000.0)
    assert len(events) == 1
    assert events[0].timestamp == 5.5
    assert events[0].raw_timestamp == 1791288005.5


def test_to_timeline_events_mixed_and_deterministic_ordering() -> None:
    speech = [
        SpeechEvent(start=10.0, end=12.0, text="First statement"),
        SpeechEvent(start=10.0, end=11.5, text="Duplicate start timestamp"),
    ]
    visual = [
        VisualEvent(timestamp=10.0, source="camera", frame_path="/tmp/c.jpg"),
        VisualEvent(timestamp=5.0, source="screen", frame_path="/tmp/s.jpg"),
    ]

    stream = EventBuilder.to_timeline_events(speech, visual)
    assert len(stream) == 4
    # Earliest event is visual at 5.0
    assert stream[0].timestamp == 5.0
    assert stream[0].source == "screen"

    # At 10.0: speech events precede visual event deterministically
    assert stream[1].timestamp == 10.0
    assert stream[1].type == "speech"
    assert stream[2].timestamp == 10.0
    assert stream[2].type == "speech"
    assert stream[3].timestamp == 10.0
    assert stream[3].source == "camera"
