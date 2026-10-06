"""Tests for LocalVectorIndex."""

import numpy as np
import pytest
from retrieval.index import LocalVectorIndex
from retrieval.schemas import ChunkType, MemoryChunk, RetrievalFilter


@pytest.fixture
def sample_chunks():
    c1 = MemoryChunk(
        chunk_id="sess1_c1",
        lecture_id="sess1",
        session_id="sess1",
        chunk_type=ChunkType.CONCEPT,
        source_item_id="c1",
        timestamp_start=10.0,
        timestamp_end=15.0,
        text="Ohm's law relates current and voltage",
        source_type="speech",
        grounding_status="trusted",
    )
    c2 = MemoryChunk(
        chunk_id="sess1_c2",
        lecture_id="sess1",
        session_id="sess1",
        chunk_type=ChunkType.EQUATION,
        source_item_id="eq1",
        timestamp_start=12.0,
        timestamp_end=17.0,
        text="I = V / R",
        source_type="multimodal",
        grounding_status="trusted",
    )
    c3 = MemoryChunk(
        chunk_id="sess2_c1",
        lecture_id="sess2",
        session_id="sess2",
        chunk_type=ChunkType.CONCEPT,
        source_item_id="c2",
        timestamp_start=5.0,
        timestamp_end=10.0,
        text="Newton's second law of motion F = ma",
        source_type="speech",
        grounding_status="trusted",
    )
    return [c1, c2, c3]


def test_1_and_2_indexing_one_and_multiple_lectures(sample_chunks):
    """Requirements 1 & 2: Indexing one and multiple lectures."""
    index = LocalVectorIndex(dimension=4)

    # Lecture 1
    e1 = np.array([[1.0, 0.0, 0.0, 0.0], [0.8, 0.6, 0.0, 0.0]], dtype=np.float32)
    index.add_lecture_chunks("sess1", sample_chunks[:2], e1)
    assert len(index.chunks) == 2

    # Lecture 2
    e2 = np.array([[0.0, 0.0, 1.0, 0.0]], dtype=np.float32)
    index.add_lecture_chunks("sess2", [sample_chunks[2]], e2)
    assert len(index.chunks) == 3


def test_5_top_k_behavior(sample_chunks):
    """Requirement 5: Top-k limits result count accurately."""
    index = LocalVectorIndex(dimension=4)
    embeds = np.array(
        [[1.0, 0.0, 0.0, 0.0], [0.9, 0.1, 0.0, 0.0], [0.8, 0.2, 0.0, 0.0]],
        dtype=np.float32,
    )
    index.add_lecture_chunks("sess1", sample_chunks, embeds)

    q = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    res_1 = index.search(q, top_k=1)
    assert len(res_1) == 1

    res_2 = index.search(q, top_k=2)
    assert len(res_2) == 2


def test_10_deterministic_rebuild(sample_chunks):
    """Requirement 10: Deterministic index rebuild."""
    index = LocalVectorIndex(dimension=4)
    embeds = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]], dtype=np.float32)
    index.add_lecture_chunks("sess1", sample_chunks, embeds)

    index.rebuild_index()
    assert "sess1" in index.session_index_map
    assert len(index.session_index_map["sess1"]) == 2
    assert "sess2" in index.session_index_map
    assert len(index.session_index_map["sess2"]) == 1


def test_11_save_load_index(tmp_path, sample_chunks):
    """Requirement 11: Save and load index to disk."""
    index = LocalVectorIndex(dimension=4)
    embeds = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]], dtype=np.float32)
    index.add_lecture_chunks("sess1", sample_chunks, embeds)

    save_dir = tmp_path / "test_vec_index"
    index.save_index(save_dir)

    loaded = LocalVectorIndex.load_index(save_dir, dimension=4)
    assert len(loaded.chunks) == 3
    assert loaded.embeddings.shape == (3, 4)
    assert "sess1" in loaded.session_index_map


def test_12_empty_index_search():
    """Requirement 12: Searching empty index returns empty list."""
    index = LocalVectorIndex(dimension=4)
    q = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    assert index.search(q) == []


def test_16_duplicate_lecture_handling(sample_chunks):
    """Requirement 16: Adding lecture with existing session_id replaces previous chunks."""
    index = LocalVectorIndex(dimension=4)
    e1 = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], dtype=np.float32)
    index.add_lecture_chunks("sess1", sample_chunks[:2], e1)
    assert len(index.chunks) == 2

    # Re-add sess1 with only 1 chunk
    e1_new = np.array([[0, 0, 0, 1]], dtype=np.float32)
    index.add_lecture_chunks("sess1", [sample_chunks[0]], e1_new)
    assert len(index.chunks) == 1
    assert index.chunks[0].chunk_id == "sess1_c1"


def test_17_lecture_deletion(sample_chunks):
    """Requirement 17: Removing a lecture deletes all associated chunks and vectors."""
    index = LocalVectorIndex(dimension=4)
    embeds = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]], dtype=np.float32)
    index.add_lecture_chunks("sess1", sample_chunks, embeds)

    assert index.remove_lecture("sess1") is True
    assert len(index.chunks) == 0
    assert index.embeddings.shape[0] == 0
    assert "sess1" not in index.session_index_map


def test_18_metadata_filtering(sample_chunks):
    """Requirement 18: Metadata filtering by source_type, chunk_type, session_id."""
    index = LocalVectorIndex(dimension=4)
    embeds = np.array([[1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0]], dtype=np.float32)
    index.add_lecture_chunks("mixed", sample_chunks, embeds)

    q = np.array([1, 0, 0, 0], dtype=np.float32)

    # Filter only equations
    filter_eq = RetrievalFilter(chunk_type=ChunkType.EQUATION)
    res_eq = index.search(q, filter_criteria=filter_eq)
    assert len(res_eq) == 1
    assert res_eq[0].chunk.chunk_type == ChunkType.EQUATION

    # Filter only multimodal source
    filter_mm = RetrievalFilter(source_type="multimodal")
    res_mm = index.search(q, filter_criteria=filter_mm)
    assert len(res_mm) == 1
    assert res_mm[0].chunk.source_type == "multimodal"
