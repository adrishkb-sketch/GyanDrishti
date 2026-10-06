"""Unit tests for Provenance tracking in Lecture Memory Engine."""

import pytest
from lecture_memory.provenance import (
    Provenance,
    create_derived_provenance,
    create_multimodal_provenance,
    create_speech_provenance,
    create_visual_provenance,
)


def test_speech_provenance_creation() -> None:
    prov = create_speech_provenance(
        start=10.0,
        end=14.5,
        text_snippet="Ohm's law relates current and voltage",
        source_id="session_01",
    )
    assert prov.source_type == "speech"
    assert prov.timestamp_start == 10.0
    assert prov.timestamp_end == 14.5
    assert prov.evidence_snippet == "Ohm's law relates current and voltage"
    assert prov.source_id == "session_01"
    assert prov.grounding_status == "supported"


def test_visual_provenance_creation() -> None:
    prov = create_visual_provenance(
        timestamp=25.2,
        frame_path="/tmp/frames/frame_001.jpg",
        event_type="keyframe",
    )
    assert prov.source_type == "visual"
    assert prov.timestamp_start == 25.2
    assert prov.source_id == "/tmp/frames/frame_001.jpg"
    assert "Visual keyframe" in prov.evidence_snippet


def test_multimodal_provenance_creation() -> None:
    prov = create_multimodal_provenance(
        start=30.0,
        end=45.0,
        speech_snippet="Teacher points to circuit on board",
        frame_path="/tmp/frames/board.jpg",
    )
    assert prov.source_type == "multimodal"
    assert prov.timestamp_start == 30.0
    assert prov.timestamp_end == 45.0
    assert "/tmp/frames/board.jpg" in prov.evidence_snippet


def test_derived_provenance_creation() -> None:
    prov = create_derived_provenance(
        start=None,
        end=None,
        evidence_snippet="Derived synthesis",
        grounding_status="supported",
    )
    assert prov.source_type == "derived"
    assert prov.timestamp_start is None
    assert prov.evidence_snippet == "Derived synthesis"


def test_invalid_source_type_rejected() -> None:
    with pytest.raises(ValueError, match="Invalid source_type"):
        Provenance(
            source_type="telepathy",
            timestamp_start=1.0,
            timestamp_end=2.0,
            evidence_snippet="Invented",
        )
