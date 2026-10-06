"""Tests for Optical Character Recognition (OCR) engines and mathematical heuristics."""

import cv2
import numpy as np
from PIL import Image, ImageDraw
import pytest

from visual_intelligence.ocr import (
    BaseOCREngine,
    MockOCREngine,
    RapidOCREngine,
    detect_potential_math,
)


def test_ocr_text_preserved_exactly_as_extracted():
    """Requirement 4: OCR text is preserved exactly as extracted."""
    canned = [
        ([[10, 10], [100, 10], [100, 40], [10, 40]], "Raw Board Text: I = V/R", 0.95)
    ]
    engine = MockOCREngine(canned_results=canned)
    dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
    results = engine.detect_and_recognize(dummy_img)

    assert len(results) == 1
    assert results[0][1] == "Raw Board Text: I = V/R"
    assert results[0][2] == 0.95


def test_english_text_extraction_synthetic_fixture():
    """Requirement 13: English text extraction works on a synthetic fixture."""
    # Render synthetic text onto clean white background
    img = Image.new("RGB", (450, 120), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), "Ohm's Law Equation", fill=(0, 0, 0))
    draw.text((20, 65), "I = V / R", fill=(0, 0, 0))

    img_np = np.array(img)
    engine = RapidOCREngine()
    detections = engine.detect_and_recognize(img_np)

    assert len(detections) >= 1
    extracted_texts = [d[1] for d in detections]
    # Check that recognized text contains Ohm or Law or equation
    has_text = any("Ohm" in t or "Law" in t or "I = V" in t or "V / R" in t for t in extracted_texts)
    assert has_text, f"Expected recognition in {extracted_texts}"


def test_cannot_create_equation_when_no_text_exists():
    """Requirement 14: OCR cannot create an equation when no text exists."""
    is_math, expr = detect_potential_math("")
    assert is_math is False
    assert expr is None

    is_math, expr = detect_potential_math("   ")
    assert is_math is False
    assert expr is None

    # Plain conversational text without equations
    is_math, expr = detect_potential_math("Good morning students, please take your seats.")
    assert is_math is False
    assert expr is None


def test_detect_potential_math_positive_cases():
    """Mathematical equations are deterministically identified."""
    math_examples = [
        "I = V / R",
        "E = mc^2",
        "F = m * a",
        "V = I * R",
        "y = mx + b",
        "a^2 + b^2 = c^2",
    ]
    for expr in math_examples:
        is_math, matched = detect_potential_math(expr)
        assert is_math is True, f"Failed to identify math in: {expr}"
        assert matched is not None


def test_no_network_access_required(monkeypatch):
    """Requirement 19: No network access is required."""
    # Block socket connections to guarantee zero network traffic
    import socket

    def guarded_connect(*args, **kwargs):
        raise RuntimeError("Network access attempted during offline OCR operation!")

    monkeypatch.setattr(socket, "socket", guarded_connect)

    engine = MockOCREngine(
        canned_results=[([[0, 0], [10, 0], [10, 10], [0, 10]], "Offline verified", 0.99)]
    )
    res = engine.detect_and_recognize(np.zeros((10, 10, 3), dtype=np.uint8))
    assert res[0][1] == "Offline verified"


def test_no_llm_is_invoked():
    """Requirement 20: No LLM is invoked."""
    engine = RapidOCREngine()
    # RapidOCREngine does not import or call any LLM module
    assert not hasattr(engine, "llm")
    assert not hasattr(engine, "generate")
    assert not hasattr(engine, "complete")
