"""Tests for Visual Intelligence Pydantic schemas."""

import pytest
from visual_intelligence.schemas import (
    BoundingBox,
    OCRStatus,
    PreprocessingVariant,
    VisualAnalysisResult,
    VisualTextEvidence,
    MultimodalAssociation,
)


def test_bounding_box_from_polygon():
    """Requirement 6: Bounding boxes validate correctly."""
    polygon = [[10.0, 20.0], [100.0, 25.0], [98.0, 60.0], [12.0, 58.0]]
    bbox = BoundingBox.from_polygon(polygon)

    assert bbox.x_min == 10.0
    assert bbox.y_min == 20.0
    assert bbox.x_max == 100.0
    assert bbox.y_max == 60.0
    assert len(bbox.polygon) == 4


def test_confidence_bounded_zero_one():
    """Requirement 5: Confidence is bounded between 0 and 1."""
    ev_high = VisualTextEvidence(
        id="ev_001",
        keyframe_id="kf_01",
        timestamp=12.5,
        text="Sample text",
        confidence=1.85,  # Exceeds 1.0, should be clamped to 1.0
        source_image="frames/f1.jpg",
    )
    assert ev_high.confidence == 1.0

    ev_low = VisualTextEvidence(
        id="ev_002",
        keyframe_id="kf_01",
        timestamp=12.5,
        text="Sample text",
        confidence=-0.45,  # Sub-zero, should be clamped to 0.0
        source_image="frames/f1.jpg",
    )
    assert ev_low.confidence == 0.0

    res = VisualAnalysisResult(
        keyframe_id="kf_01",
        timestamp=12.5,
        source_image="frames/f1.jpg",
        overall_confidence=1.5,
    )
    assert res.overall_confidence == 1.0


def test_ocr_result_schema_correctness():
    """Requirement 3: OCR result has correct schema."""
    bbox = BoundingBox.from_polygon([[0, 0], [10, 0], [10, 10], [0, 10]])
    item = VisualTextEvidence(
        id="ev_101",
        session_id="session_test_01",
        keyframe_id="kf_001",
        timestamp=14.2,
        text="I = V / R",
        confidence=0.92,
        bounding_box=bbox,
        preprocessing_variant="clahe",
        source_image="output_frames/kf_001.jpg",
        is_potential_math=True,
    )
    assert item.keyframe_id == "kf_001"
    assert item.timestamp == 14.2
    assert item.is_potential_math is True

    result = VisualAnalysisResult(
        keyframe_id="kf_001",
        timestamp=14.2,
        source_image="output_frames/kf_001.jpg",
        extracted_text=[item],
        raw_text_combined="I = V / R",
        overall_confidence=0.92,
        processing_status=OCRStatus.SUCCESS,
        potential_equations=["I = V / R"],
        warnings=[],
        latency_ms=45.2,
        image_dimensions={"width": 640, "height": 480},
    )
    dumped = result.model_dump()
    assert dumped["processing_status"] == "success"
    assert dumped["extracted_text"][0]["text"] == "I = V / R"
    assert dumped["image_dimensions"]["width"] == 640


def test_unicode_text_support():
    """Requirement 12: Unicode text works (English, Hindi, Bengali)."""
    texts = [
        "Ohm's Law: I = V / R",
        "ओम का नियम: धारा = विभव / प्रतिरोध",
        "ওহমের সূত্র: তড়িৎ প্রবাহ = বিভব / রোধ",
    ]
    for idx, txt in enumerate(texts):
        ev = VisualTextEvidence(
            id=f"unicode_{idx}",
            keyframe_id=f"kf_{idx}",
            timestamp=float(idx * 5),
            text=txt,
            confidence=0.88,
            source_image="frame.jpg",
        )
        assert ev.text == txt
        json_repr = ev.model_dump_json()
        restored = VisualTextEvidence.model_validate_json(json_repr)
        assert restored.text == txt
