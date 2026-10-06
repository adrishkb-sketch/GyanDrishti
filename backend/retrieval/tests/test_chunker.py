"""Tests for LectureMemoryChunker."""

import pytest
from lecture_memory.schemas import (
    LectureMemory,
    MemoryConcept,
    MemoryEquation,
    MemoryVisualReference,
    Provenance,
)
from retrieval.chunker import LectureMemoryChunker
from retrieval.schemas import ChunkType


@pytest.fixture
def sample_lecture_memory():
    prov_sp = Provenance(
        source_type="speech",
        timestamp_start=10.0,
        timestamp_end=15.0,
        evidence_snippet="Ohm's law relates current and voltage",
    )
    prov_vis = Provenance(
        source_type="visual",
        timestamp_start=20.0,
        timestamp_end=20.0,
        local_frame_reference="frames/f02.jpg",
    )

    return LectureMemory(
        session_id="sess_ohm_01",
        title="Ohm's Law Lecture",
        overview="Introduction to circuit theory.",
        concepts=[
            MemoryConcept(
                id="c_01",
                name="Ohm's Law",
                explanation="Current is proportional to voltage across a conductor.",
                timestamp=10.0,
                timestamp_start=10.0,
                timestamp_end=15.0,
                provenance=prov_sp,
            )
        ],
        equations=[
            MemoryEquation(
                name="Ohm's Formula",
                representation="I = V / R",
                explanation="Calculates current given voltage and resistance.",
                timestamp=12.0,
                grounding_status="supported",
                provenance=prov_sp,
            )
        ],
        rejected_equations=[
            MemoryEquation(
                name="Hallucinated Equation",
                representation="E = m * c^2",
                explanation="Rejected by grounding validator.",
                timestamp=14.0,
                grounding_status="unsupported",
                provenance=prov_sp,
            )
        ],
        visual_references=[
            MemoryVisualReference(
                timestamp=20.0,
                source="Camera",
                event_type="Board Writing",
                local_frame_reference="frames/f02.jpg",
                extracted_text="Board schematic of resistor",
                ocr_status="success",
                provenance=prov_vis,
            )
        ],
    )


def test_8_rejected_equation_excluded(sample_lecture_memory):
    """Requirement 8: rejected equations MUST NEVER be indexed into memory chunks."""
    chunks = LectureMemoryChunker.chunk_lecture(sample_lecture_memory)
    chunk_texts = [c.text for c in chunks]

    # Verified equation is included
    assert any("I = V / R" in t for t in chunk_texts)
    # Rejected equation is completely absent
    assert not any("E = m * c^2" in t for t in chunk_texts)
    assert not any("Hallucinated" in t for t in chunk_texts)


def test_9_visual_only_evidence_retains_source_type(sample_lecture_memory):
    """Requirement 9: visual-only evidence strictly retains source_type='visual'."""
    chunks = LectureMemoryChunker.chunk_lecture(sample_lecture_memory)
    vis_chunks = [c for c in chunks if c.chunk_type == ChunkType.VISUAL_EXPLANATION]

    assert len(vis_chunks) == 1
    assert vis_chunks[0].source_type == "visual"
    assert "Board schematic" in vis_chunks[0].text
    # Does not claim it was spoken
    assert vis_chunks[0].source_type != "speech"
