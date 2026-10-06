"""Tests for ImagePreprocessor filters in Visual Intelligence."""

import cv2
import numpy as np
import pytest
from visual_intelligence.preprocessing import ImagePreprocessor
from visual_intelligence.schemas import PreprocessingVariant


def test_grayscale_conversion():
    preprocessor = ImagePreprocessor()
    bgr_img = np.zeros((100, 100, 3), dtype=np.uint8)
    bgr_img[:, :] = (120, 80, 50)

    gray = preprocessor.to_grayscale(bgr_img)
    assert len(gray.shape) == 2
    assert gray.shape == (100, 100)


def test_blackboard_detection_and_inversion():
    preprocessor = ImagePreprocessor()

    # Dark background simulating blackboard (mean intensity 30 < 100)
    blackboard = np.full((100, 100), 30, dtype=np.uint8)
    # White chalk stroke
    blackboard[40:60, 40:60] = 240

    inverted, is_blackboard = preprocessor.detect_and_invert_blackboard(blackboard)
    assert is_blackboard is True
    # Inverted background should now be light (~225)
    assert np.mean(inverted) > 150

    # Light background simulating whiteboard (mean intensity 230 > 100)
    whiteboard = np.full((100, 100), 230, dtype=np.uint8)
    not_inverted, is_bb = preprocessor.detect_and_invert_blackboard(whiteboard)
    assert is_bb is False
    assert np.array_equal(not_inverted, whiteboard)


def test_clahe_enhancement():
    preprocessor = ImagePreprocessor()
    gray = np.full((100, 100), 128, dtype=np.uint8)
    enhanced = preprocessor.apply_clahe(gray)
    assert enhanced.shape == (100, 100)
    assert enhanced.dtype == np.uint8


def test_resize_if_needed():
    preprocessor = ImagePreprocessor(max_dimension=1000)
    large_img = np.zeros((2000, 4000, 3), dtype=np.uint8)
    resized = preprocessor.resize_if_needed(large_img)
    h, w = resized.shape[:2]
    assert max(h, w) <= 1000
    assert w == 1000
    assert h == 500


def test_prepare_variants():
    preprocessor = ImagePreprocessor()
    test_img = np.zeros((100, 100, 3), dtype=np.uint8)
    variants = preprocessor.prepare_variants(test_img)
    assert "original" in variants
    assert "grayscale" in variants
    assert "clahe" in variants
    assert "inverted_blackboard" in variants  # Dark image triggers blackboard variant
