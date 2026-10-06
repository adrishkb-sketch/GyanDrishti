"""Tests for SemanticLectureRetriever end-to-end retrieval."""

import pytest
from lecture_memory.schemas import (
    LectureMemory,
    MemoryConcept,
    MemoryEquation,
    Provenance,
)
from retrieval.retriever import SemanticLectureRetriever
from retrieval.schemas import ChunkType


@pytest.fixture
def sample_lecture():
    prov = Provenance(
        source_type="speech",
        timestamp_start=15.0,
        timestamp_end=20.0,
        evidence_snippet="Ohm's law states that current is proportional to voltage.",
    )
    return LectureMemory(
        session_id="lecture_physics_101",
        title="Electromagnetism and Circuit Laws",
        overview="Introduction to Ohm's law and basic circuit analysis.",
        concepts=[
            MemoryConcept(
                id="c_ohm",
                name="Ohm's Law",
                explanation="Ohm's law states that current through a conductor is directly proportional to voltage.",
                timestamp=15.0,
                timestamp_start=15.0,
                timestamp_end=20.0,
                provenance=prov,
            ),
            MemoryConcept(
                id="c_newton",
                name="Newton's First Law",
                explanation="An object remains at rest unless acted upon by an external force.",
                timestamp=45.0,
                timestamp_start=45.0,
                timestamp_end=50.0,
                provenance=prov,
            ),
        ],
        equations=[
            MemoryEquation(
                name="Ohm's Law Equation",
                representation="I = V / R",
                explanation="Current equals voltage divided by resistance.",
                timestamp=18.0,
                grounding_status="supported",
                provenance=prov,
            )
        ],
    )


def test_3_retrieval_of_relevant_concept(sample_lecture):
    """Requirement 3: Natural language query retrieves relevant concept."""
    retriever = SemanticLectureRetriever()
    retriever.index_lecture(sample_lecture)

    results = retriever.search("What is Ohm's law?", top_k=2)
    assert len(results) >= 1
    top_result = results[0]

    # Top result is Ohm's Law concept or equation
    assert "ohm" in top_result.chunk.text.lower()
    assert top_result.score > 0.25


def test_4_irrelevant_query_low_relevance(sample_lecture):
    """Requirement 4: Irrelevant query scores significantly lower than relevant query."""
    retriever = SemanticLectureRetriever()
    retriever.index_lecture(sample_lecture)

    res_relevant = retriever.search("What did teacher say about Ohm's law and current?", top_k=1)
    res_irrelevant = retriever.search("Photosynthesis in green plants chloroplasts", top_k=1)

    assert len(res_relevant) > 0
    assert len(res_irrelevant) > 0
    # Relevant score should be strictly higher than unrelated biology query
    assert res_relevant[0].score > res_irrelevant[0].score


def test_6_and_7_timestamps_and_provenance_preserved(sample_lecture):
    """Requirements 6 & 7: Timestamps and provenance strictly preserved on search results."""
    retriever = SemanticLectureRetriever()
    retriever.index_lecture(sample_lecture)

    results = retriever.search("I = V / R equation", top_k=1)
    assert len(results) == 1
    top = results[0].chunk

    assert top.timestamp_start >= 15.0
    assert top.session_id == "lecture_physics_101"
    assert top.provenance is not None
    assert top.provenance.get("source_type") == "speech"
