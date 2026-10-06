"""Tests for VisualReasoningAnalyzer coordination and evidence fidelity."""

import pytest
from visual_reasoning.analyzer import VisualReasoningAnalyzer
from visual_reasoning.provider import MockVLMProvider
from visual_reasoning.schemas import VLMValidationStatus


def test_9_provenance_preservation():
    """Requirement 9: Provenance source is explicitly tagged as visual_vlm."""
    analyzer = VisualReasoningAnalyzer(provider=MockVLMProvider())
    res = analyzer.analyze_keyframe(
        image_path="recordings/circuit.jpg",
        keyframe_id="kf_circ_01",
        timestamp=14.5,
        session_id="sess_01",
    )
    assert res.provenance_source == "visual_vlm"
    assert res.id == "vr_kf_circ_01"


def test_10_timestamp_preservation():
    """Requirement 10: Keyframe timestamp is preserved exactly without drift."""
    analyzer = VisualReasoningAnalyzer(provider=MockVLMProvider())
    res = analyzer.analyze_keyframe(
        image_path="recordings/kf42.jpg",
        keyframe_id="kf42",
        timestamp=42.75,
    )
    assert res.timestamp == 42.75


def test_11_no_raw_evidence_mutation():
    """Requirement 11: Raw OCR text is never overwritten or mutated by VLM output."""
    raw_ocr = "Immutable Board OCR: I = V / R"
    analyzer = VisualReasoningAnalyzer(provider=MockVLMProvider())
    res = analyzer.analyze_keyframe(
        image_path="recordings/kf_exact.jpg",
        keyframe_id="kf_exact",
        timestamp=20.0,
        raw_ocr_text=raw_ocr,
        ocr_equations=["I = V / R"],
    )
    # The raw_ocr_text field remains identical to the input
    assert res.raw_ocr_text == raw_ocr
    assert res.validation_status == VLMValidationStatus.VALIDATED
