"""Unit tests for LectureTimeline and TimelineBuilder in Temporal Engine."""

import json
from pathlib import Path
import pytest
from temporal_engine.schemas import SpeechEvent, VisualEvent
from temporal_engine.timeline import TimelineBuilder, create_lecture_timeline


def test_timeline_construction_and_source_text_preservation(tmp_path: Path) -> None:
    raw_bengali_speech = "এখানে আমরা basically দেখছি যে current টা increase করছে।"
    raw_hindi_speech = "अब हम Faraday के law के बारे में पढ़ेंगे।"

    speech_source = {
        "lecture_id": "lec_physics_01",
        "segments": [
            {"start": 5.0, "end": 8.5, "text": raw_bengali_speech, "language": ["bn", "en"]},
            {"start": 15.0, "end": 19.0, "text": raw_hindi_speech, "language": ["hi", "en"]},
        ],
    }

    visual_source = {
        "session_id": "lec_physics_01",
        "events": [
            {"timestamp": 6.2, "source": "camera", "type": "keyframe", "frame_path": "/tmp/board_f1.jpg"},
            {"timestamp": 16.5, "source": "screen", "type": "keyframe", "frame_path": "/tmp/slide_f2.jpg"},
        ],
    }

    timeline = create_lecture_timeline(
        speech_source=speech_source,
        visual_source=visual_source,
        lecture_id="lec_physics_01",
        window_before=5.0,
        window_after=5.0,
    )

    assert timeline.lecture_id == "lec_physics_01"
    assert timeline.total_speech_events == 2
    assert timeline.total_visual_events == 2
    assert len(timeline.chronological_stream) == 4
    assert len(timeline.synchronized_events) == 2

    # Verify source transcripts are strictly untouched
    assert timeline.synchronized_events[0].speech[0].text == raw_bengali_speech
    assert timeline.synchronized_events[1].speech[0].text == raw_hindi_speech

    # Verify visual associations
    assert len(timeline.synchronized_events[0].visual_events) == 1
    assert timeline.synchronized_events[0].visual_events[0].frame_path == "/tmp/board_f1.jpg"

    assert len(timeline.synchronized_events[1].visual_events) == 1
    assert timeline.synchronized_events[1].visual_events[0].frame_path == "/tmp/slide_f2.jpg"

    # Test JSON serialization and round-trip
    out_file = tmp_path / "test_timeline.json"
    timeline.save_json(out_file)
    assert out_file.is_file()

    with open(out_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["lecture_id"] == "lec_physics_01"
    assert len(data["synchronized_events"]) == 2


def test_timeline_range_and_keyframes_filter() -> None:
    speech = [
        SpeechEvent(start=10.0, end=15.0, text="Intro"),
        SpeechEvent(start=30.0, end=35.0, text="Conclusion"),
    ]
    visual = [
        VisualEvent(timestamp=12.0, source="camera", frame_path="/tmp/f1.jpg"),
        VisualEvent(timestamp=32.0, source="screen", frame_path="/tmp/f2.jpg"),
    ]

    builder = TimelineBuilder()
    timeline = builder.build_timeline(
        speech_source=speech,
        visual_source=visual,
        lecture_id="filter_test",
    )

    # Range filter [5.0, 20.0] should only return first speech and first visual
    events_in_range = timeline.get_events_in_range(5.0, 20.0)
    assert len(events_in_range) == 2
    assert events_in_range[0].timestamp == 10.0
    assert events_in_range[1].timestamp == 12.0

    # Keyframes helper
    keyframes = timeline.get_keyframes()
    assert len(keyframes) == 2
    assert {k.frame_path for k in keyframes} == {"/tmp/f1.jpg", "/tmp/f2.jpg"}


def test_timeline_determinism() -> None:
    # Identical inputs must yield identical outputs
    speech = [SpeechEvent(start=5.0, end=8.0, text="Deterministic text")]
    visual = [VisualEvent(timestamp=6.0, source="camera", frame_path="/tmp/c.jpg")]

    builder = TimelineBuilder()
    t1 = builder.build_timeline(speech, visual)
    t2 = builder.build_timeline(speech, visual)

    assert t1.model_dump(exclude={"created_at"}) == t2.model_dump(exclude={"created_at"})
    assert len(t1.chronological_stream) == len(t2.chronological_stream)
    assert len(t1.synchronized_events) == len(t2.synchronized_events)
