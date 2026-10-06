"""Unit tests for JSON extraction and validation module."""

import pytest
from understanding_engine.validators import (
    UnderstandingValidationError,
    extract_json_from_llm_text,
    validate_and_build_understanding,
)


def test_extract_json_from_markdown_codeblock() -> None:
    text = """Here is the lecture understanding:
```json
{
  "topic": "Electromagnetic Induction",
  "concepts": []
}
```
Hope this helps!"""
    res = extract_json_from_llm_text(text)
    assert res["topic"] == "Electromagnetic Induction"


def test_extract_json_direct() -> None:
    text = '{"topic": "Faraday Law", "concepts": []}'
    res = extract_json_from_llm_text(text)
    assert res["topic"] == "Faraday Law"


def test_extract_json_empty_raises_error() -> None:
    with pytest.raises(UnderstandingValidationError, match="Empty output"):
        extract_json_from_llm_text("")


def test_extract_json_malformed_raises_error() -> None:
    with pytest.raises(UnderstandingValidationError):
        extract_json_from_llm_text("This text has { no closing brace")


def test_validate_and_build_understanding_sanitizes_partial_fields() -> None:
    raw = {
        "topic": "Current Law",
        "concepts": [
            {"name": "Valid Concept", "explanation": "Valid", "timestamp_start": 5.0, "timestamp_end": 10.0},
            {"invalid_field": 123},  # Should be skipped safely without crashing
        ],
        "equations": [
            {"latex_or_text": "V = I * R", "description": "Ohm's Law", "timestamp": 6.0}
        ],
    }

    understanding = validate_and_build_understanding(
        raw_dict=raw,
        fallback_start=0.0,
        fallback_end=15.0,
        lecture_id="lec_safe",
        raw_transcript_ref="Source text",
    )

    assert understanding.topic == "Current Law"
    assert len(understanding.concepts) == 1
    assert understanding.concepts[0].name == "Valid Concept"
    assert len(understanding.equations) == 1
    assert understanding.equations[0].latex_or_text == "V = I * R"
    assert understanding.raw_transcript_ref == "Source text"
