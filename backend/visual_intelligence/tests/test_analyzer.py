"""Tests for VisualIntelligenceAnalyzer."""

import os
import cv2
import numpy as np
import pytest

from visual_intelligence.analyzer import VisualIntelligenceAnalyzer
from visual_intelligence.ocr import MockOCREngine
from visual_intelligence.schemas import OCRStatus


def test_1_valid_keyframe_analyzed(tmp_path):
    """Requirement 1: Valid keyframe can be analyzed."""
    img_path = str(tmp_path / "valid_frame.jpg")
    img = np.full((100, 200, 3), 255, dtype=np.uint8)
    cv2.imwrite(img_path, img)

    mock_engine = MockOCREngine(
        canned_results=[
            ([[10, 10], [90, 10], [90, 40], [10, 40]], "Lecture Note: Circuit Analysis", 0.94)
        ]
    )
    analyzer = VisualIntelligenceAnalyzer(ocr_engine=mock_engine)
    res = analyzer.analyze_image(
        image_input=img_path,
        keyframe_id="kf_001",
        timestamp=12.5,
        session_id="sess_01",
    )

    assert res.processing_status == OCRStatus.SUCCESS
    assert len(res.extracted_text) == 1
    assert res.extracted_text[0].text == "Lecture Note: Circuit Analysis"
    assert res.overall_confidence == 0.94


def test_2_missing_image_produces_clear_status():
    """Requirement 2: Missing image produces a clear error/status."""
    analyzer = VisualIntelligenceAnalyzer()
    res = analyzer.analyze_image(
        image_input="/nonexistent/path/to/missing_frame.jpg",
        keyframe_id="kf_missing",
        timestamp=8.0,
    )
    assert res.processing_status == OCRStatus.IMAGE_NOT_FOUND
    assert len(res.extracted_text) == 0
    assert any("does not exist" in w for w in res.warnings)


def test_7_empty_ocr_does_not_create_fake_text(tmp_path):
    """Requirement 7: Empty OCR result does not create fake text."""
    blank_path = str(tmp_path / "blank.jpg")
    cv2.imwrite(blank_path, np.full((100, 100, 3), 255, dtype=np.uint8))

    empty_engine = MockOCREngine(canned_results=[])
    analyzer = VisualIntelligenceAnalyzer(ocr_engine=empty_engine)
    res = analyzer.analyze_image(
        image_input=blank_path,
        keyframe_id="kf_blank",
        timestamp=5.0,
    )

    assert res.processing_status == OCRStatus.NO_TEXT_DETECTED
    assert res.extracted_text == []
    assert res.raw_text_combined == ""
    assert res.potential_equations == []


def test_8_ocr_failure_preserves_metadata(tmp_path):
    """Requirement 8 & 17: Failed OCR produces safe status rather than hallucinated content."""
    img_path = str(tmp_path / "corrupt.jpg")
    cv2.imwrite(img_path, np.full((100, 100, 3), 255, dtype=np.uint8))

    failing_engine = MockOCREngine(should_fail=True)
    analyzer = VisualIntelligenceAnalyzer(ocr_engine=failing_engine)
    res = analyzer.analyze_image(
        image_input=img_path,
        keyframe_id="kf_fail",
        timestamp=20.0,
    )

    assert res.processing_status == OCRStatus.FAILED
    assert res.extracted_text == []
    assert any("OCR engine failure" in w for w in res.warnings)
    # Original metadata is preserved
    assert res.keyframe_id == "kf_fail"
    assert res.timestamp == 20.0
    assert res.source_image == img_path


def test_9_10_11_preserves_keyframe_id_timestamp_and_path(tmp_path):
    """Requirements 9, 10, 11: Existing keyframe ID, timestamp, and frame path are preserved."""
    test_path = str(tmp_path / "frame_sample.jpg")
    cv2.imwrite(test_path, np.full((100, 100, 3), 255, dtype=np.uint8))

    mock_engine = MockOCREngine(
        canned_results=[([[0, 0], [10, 0], [10, 10], [0, 10]], "Test", 0.9)]
    )
    analyzer = VisualIntelligenceAnalyzer(ocr_engine=mock_engine)
    res = analyzer.analyze_image(
        image_input=test_path,
        keyframe_id="camera_f042_15200",
        timestamp=15.2,
    )

    assert res.keyframe_id == "camera_f042_15200"  # Requirement 9
    assert res.timestamp == 15.2                  # Requirement 10
    assert res.source_image == test_path           # Requirement 11


def test_15_ocr_remains_visually_sourced_not_speech_sourced(tmp_path):
    """Requirement 15: OCR output remains visually sourced, not speech-sourced."""
    img_path = str(tmp_path / "board_formula.jpg")
    cv2.imwrite(img_path, np.full((100, 100, 3), 255, dtype=np.uint8))

    mock_engine = MockOCREngine(
        canned_results=[([[0, 0], [50, 0], [50, 20], [0, 20]], "V = I * R", 0.91)]
    )
    analyzer = VisualIntelligenceAnalyzer(ocr_engine=mock_engine)
    res = analyzer.analyze_image(img_path, keyframe_id="kf_board", timestamp=30.0)

    for item in res.extracted_text:
        assert item.source_image == img_path
        assert item.keyframe_id == "kf_board"
        assert item.text == "V = I * R"
