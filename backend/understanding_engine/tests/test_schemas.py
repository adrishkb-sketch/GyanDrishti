"""Unit tests for Understanding Engine schemas."""

from pathlib import Path
import pytest
from understanding_engine.schemas import (
    Concept,
    Definition,
    Equation,
    ImportantPoint,
    LectureUnderstanding,
    QuestionCandidate,
    VisualReference,
)


def test_concept_schema_and_rounding() -> None:
    c = Concept(
        name="Ohm's Law",
        explanation="Relates voltage, current, and resistance in an electrical circuit.",
        timestamp_start=10.258,
        timestamp_end=15.894,
    )
    assert c.name == "Ohm's Law"
    assert c.timestamp_start == 10.26
    assert c.timestamp_end == 15.89


def test_equation_schema_and_flags() -> None:
    eq = Equation(
        latex_or_text="I = V / R",
        description="Current is directly proportional to voltage and inversely to resistance",
        timestamp=12.5,
        explicitly_spoken=True,
    )
    assert eq.latex_or_text == "I = V / R"
    assert eq.explicitly_spoken is True


def test_visual_reference_schema() -> None:
    vr = VisualReference(
        timestamp=11.341,
        source="camera",
        event_type="keyframe",
        frame_path="/tmp/frame.jpg",
        relevance="Circuit diagram on the blackboard.",
    )
    assert vr.timestamp == 11.34
    assert vr.source == "camera"
    assert vr.frame_path == "/tmp/frame.jpg"


def test_lecture_understanding_json_roundtrip(tmp_path: Path) -> None:
    raw_source = "Ekhane amra basically dekhchi je current ta increase korche."
    understanding = LectureUnderstanding(
        lecture_id="lec_001",
        time_start=10.0,
        time_end=25.0,
        topic="Current Dynamics",
        concepts=[
            Concept(
                name="Current Resistance Inverse Relation",
                explanation="Current increases when resistance decreases.",
                timestamp_start=10.0,
                timestamp_end=25.0,
            )
        ],
        definitions=[
            Definition(
                term="Current",
                definition="Rate of flow of charge.",
                timestamp=11.0,
            )
        ],
        equations=[
            Equation(
                latex_or_text="I = V / R",
                description="Ohm's Law",
                timestamp=14.0,
            )
        ],
        important_points=[
            ImportantPoint(
                point="Current increases as resistance decreases under constant voltage.",
                timestamp_start=10.0,
                timestamp_end=20.0,
            )
        ],
        visual_references=[
            VisualReference(
                timestamp=12.0,
                source="camera",
                frame_path="/tmp/board.jpg",
                relevance="Board diagram.",
            )
        ],
        question_candidates=[
            QuestionCandidate(
                question="What happens to current if resistance decreases?",
                expected_answer="Current increases.",
                relevant_timestamp=15.0,
            )
        ],
        raw_transcript_ref=raw_source,
    )

    json_str = understanding.to_json()
    assert "Current Dynamics" in json_str
    assert raw_source in json_str

    out_file = tmp_path / "understanding.json"
    understanding.save_json(out_file)
    assert out_file.is_file()
