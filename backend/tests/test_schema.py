"""Unit tests for Pydantic schemas and serialization."""

import json
import pytest
from speech_engine.schemas import TranscriptionResult, TranscriptionSegment


def test_segment_schema_valid() -> None:
    seg = TranscriptionSegment(
        id=1,
        start=0.0123,
        end=4.8291,
        text="Today we're going to study electromagnetic induction.",
        language=["en"],
        confidence=None,
    )
    assert seg.id == 1
    assert seg.start == 0.01
    assert seg.end == 4.83
    assert seg.text.startswith("Today")
    assert seg.language == ["en"]
    assert seg.confidence is None


def test_result_schema_and_json_export(tmp_path) -> None:
    seg1 = TranscriptionSegment(
        id=1,
        start=0.0,
        end=4.82,
        text="Today we're going to study electromagnetic induction.",
        language=["en"],
        confidence=None,
    )
    seg2 = TranscriptionSegment(
        id=2,
        start=5.10,
        end=9.72,
        text="अब हम Faraday's law के बारे में पढ़ेंगे।",
        language=["hi", "en"],
        confidence=None,
    )

    result = TranscriptionResult(
        lecture_id="lec-001",
        duration=10.0,
        processing_time=2.5,
        real_time_factor=0.25,
        model_name="small",
        device="cpu",
        compute_type="int8",
        language_summary=["en", "hi"],
        segments=[seg1, seg2],
        raw_text="Today we're going to study electromagnetic induction. अब हम Faraday's law के बारे में पढ़ेंगे।",
    )

    json_str = result.to_json()
    parsed = json.loads(json_str)

    assert parsed["lecture_id"] == "lec-001"
    assert parsed["real_time_factor"] == 0.25
    assert len(parsed["segments"]) == 2
    assert parsed["segments"][0]["confidence"] is None
    assert parsed["segments"][1]["language"] == ["hi", "en"]

    out_file = tmp_path / "transcript.json"
    result.save_json(out_file)
    assert out_file.is_file()

    with open(out_file, "r", encoding="utf-8") as f:
        file_json = json.load(f)
    assert file_json["lecture_id"] == "lec-001"
