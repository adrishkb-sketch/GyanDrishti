"""Tests for VisualEvidenceStorage local persistence."""

import json
import pytest
from visual_intelligence.schemas import OCRStatus, VisualAnalysisResult, VisualTextEvidence
from visual_intelligence.storage import (
    CorruptResultsError,
    InvalidSessionIdError,
    ResultsNotFoundError,
    VisualEvidenceStorage,
)


def test_storage_save_and_load(tmp_path):
    storage = VisualEvidenceStorage(base_dir=str(tmp_path))
    session_id = "test_session_20261006"

    item = VisualTextEvidence(
        id="ev_01",
        keyframe_id="kf_01",
        timestamp=10.0,
        text="I = V / R",
        confidence=0.95,
        source_image="frames/f01.jpg",
        is_potential_math=True,
    )
    result = VisualAnalysisResult(
        keyframe_id="kf_01",
        timestamp=10.0,
        source_image="frames/f01.jpg",
        extracted_text=[item],
        raw_text_combined="I = V / R",
        overall_confidence=0.95,
        processing_status=OCRStatus.SUCCESS,
        potential_equations=["I = V / R"],
    )

    saved_path = storage.save_results(session_id, [result])
    assert saved_path.exists()

    loaded = storage.load_results(session_id)
    assert len(loaded) == 1
    assert loaded[0].keyframe_id == "kf_01"
    assert loaded[0].extracted_text[0].text == "I = V / R"
    assert loaded[0].overall_confidence == 0.95


def test_storage_invalid_session_traversal(tmp_path):
    storage = VisualEvidenceStorage(base_dir=str(tmp_path))
    with pytest.raises(InvalidSessionIdError):
        storage.save_results("../escape_dir", [])

    with pytest.raises(InvalidSessionIdError):
        storage.load_results("bad/path/id")


def test_storage_not_found(tmp_path):
    storage = VisualEvidenceStorage(base_dir=str(tmp_path))
    with pytest.raises(ResultsNotFoundError):
        storage.load_results("nonexistent_session")


def test_storage_corrupt_file(tmp_path):
    storage = VisualEvidenceStorage(base_dir=str(tmp_path))
    s_dir = storage.get_session_dir("corrupt_sess")
    target = s_dir / "visual_analysis.json"
    with open(target, "w", encoding="utf-8") as f:
        f.write("{invalid json content")

    with pytest.raises(CorruptResultsError):
        storage.load_results("corrupt_sess")
