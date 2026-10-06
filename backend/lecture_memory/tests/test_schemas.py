"""Unit tests for Lecture Memory schemas (Milestone 5)."""

import pytest
from lecture_memory.provenance import create_speech_provenance
from lecture_memory.schemas import (
    LectureMemory,
    LectureMetadata,
    MemoryConcept,
    MemoryDefinition,
    MemoryEquation,
    MemoryImportantPoint,
    MemoryQuestionCandidate,
    MemoryTimelineEvent,
    MemoryVisualReference,
)


def test_schema_version_exists() -> None:
    """TEST 16: Schema version exists."""
    memory = LectureMemory(
        session_id="session_test",
        title="Test Lecture",
        overview="Overview text",
    )
    assert memory.schema_version == "1.0.0"


def test_serialization_deserialization_lossless() -> None:
    """TEST 12: LectureMemory serialization/deserialization is lossless."""
    prov = create_speech_provenance(start=10.0, end=15.0, text_snippet="Ohm's Law explained")
    concept = MemoryConcept(
        id="c1",
        name="Ohm's Law",
        explanation="Current proportional to voltage",
        timestamp=10.0,
        timestamp_start=10.0,
        timestamp_end=15.0,
        provenance=prov,
    )
    eq = MemoryEquation(
        name="Ohm's Law",
        representation="I = V / R",
        explanation="Current is voltage over resistance",
        timestamp=12.0,
        provenance=prov,
    )
    memory = LectureMemory(
        session_id="session_lossless",
        title="Electromagnetism Basics",
        subject="Physics",
        date="October 6, 2026",
        duration=120.5,
        overview="Lecture introducing basic circuit laws.",
        concepts=[concept],
        equations=[eq],
    )

    json_str = memory.to_json()
    loaded = LectureMemory.from_json(json_str)

    assert loaded.session_id == memory.session_id
    assert loaded.title == memory.title
    assert loaded.duration == memory.duration
    assert len(loaded.concepts) == 1
    assert loaded.concepts[0].name == "Ohm's Law"
    assert loaded.concepts[0].provenance.evidence_snippet == "Ohm's Law explained"
    assert len(loaded.equations) == 1
    assert loaded.equations[0].representation == "I = V / R"


def test_frontend_dict_shape_conformance() -> None:
    """Verifies that to_frontend_dict conforms directly with src/types/lectureMemory.d.ts."""
    prov = create_speech_provenance(start=5.0, end=10.0, text_snippet="Circuit introduction")
    memory = LectureMemory(
        session_id="session_ui",
        title="Circuit Analysis",
        subject="EE 101",
        date="October 6, 2026",
        duration=300.0,
        overview="Circuit theory overview",
        concepts=[
            MemoryConcept(
                id="c1",
                name="Kirchhoff's Voltage Law",
                explanation="Sum of voltages is zero",
                timestamp=5.0,
                timestamp_start=5.0,
                timestamp_end=10.0,
                provenance=prov,
            )
        ],
        equations=[
            MemoryEquation(
                name="KVL",
                representation="\\sum V = 0",
                explanation="Loop voltage law",
                timestamp=8.0,
                provenance=prov,
            )
        ],
    )

    fe_dict = memory.to_frontend_dict()
    assert fe_dict["session_id"] == "session_ui"
    assert fe_dict["title"] == "Circuit Analysis"
    assert fe_dict["subject"] == "EE 101"
    assert fe_dict["storage_local"] is True
    assert isinstance(fe_dict["duration"], int)
    assert len(fe_dict["concepts"]) == 1
    assert fe_dict["concepts"][0]["id"] == "c1"
    assert len(fe_dict["equations"]) == 1
    assert fe_dict["equations"][0]["representation"] == "\\sum V = 0"
