"""Tests for VisualReasoningValidator rules and conflict detection."""

import pytest
from visual_reasoning.schemas import (
    DiagramType,
    VLMValidationStatus,
    VisualReasoningProposal,
)
from visual_reasoning.validators import VisualReasoningValidator


def test_5_empty_image():
    """Requirement 5: empty image yields EMPTY_IMAGE status."""
    validator = VisualReasoningValidator()
    status, notes = validator.validate_proposal(None, is_empty_image=True)
    assert status == VLMValidationStatus.EMPTY_IMAGE


def test_6_ocr_vlm_agreement():
    """Requirement 6: OCR + VLM agreement produces VALIDATED status."""
    validator = VisualReasoningValidator()
    proposal = VisualReasoningProposal(
        model_name="mock-vlm",
        diagram_type=DiagramType.CIRCUIT_DIAGRAM,
        description="Circuit diagram with Ohm's law.",
        visible_equations=["I = V / R"],
        confidence=0.9,
    )
    status, notes = validator.validate_proposal(
        proposal=proposal,
        raw_ocr_text="I = V / R",
        ocr_equations=["I = V / R"],
    )
    assert status == VLMValidationStatus.VALIDATED
    assert "agree" in notes.lower()


def test_7_ocr_vlm_disagreement_conflict():
    """Requirement 7: OCR + VLM disagreement produces OCR_CONFLICT, preserving raw OCR."""
    validator = VisualReasoningValidator()
    proposal = VisualReasoningProposal(
        model_name="mock-vlm",
        diagram_type=DiagramType.CIRCUIT_DIAGRAM,
        description="Circuit diagram claims I = V * R.",
        visible_equations=["I = V * R"],  # Conflicting with OCR ground truth
        confidence=0.85,
    )
    status, notes = validator.validate_proposal(
        proposal=proposal,
        raw_ocr_text="Verified Board: I = V / R",
        ocr_equations=["I = V / R"],
    )
    assert status == VLMValidationStatus.OCR_CONFLICT
    assert "contradicts OCR ground truth" in notes


def test_8_vlm_only_diagram_understanding():
    """Requirement 8: VLM-only diagram understanding (e.g. schematic with no text)."""
    validator = VisualReasoningValidator()
    proposal = VisualReasoningProposal(
        model_name="mock-vlm",
        diagram_type=DiagramType.CIRCUIT_DIAGRAM,
        description="Unlabeled battery connected to resistor loop.",
        entities_detected=["Battery", "Resistor"],
        visible_equations=[],  # No text/equations on board
        confidence=0.82,
    )
    status, notes = validator.validate_proposal(
        proposal=proposal,
        raw_ocr_text="",
        ocr_equations=[],
    )
    assert status == VLMValidationStatus.PROPOSED
    assert "circuit_diagram" in notes
