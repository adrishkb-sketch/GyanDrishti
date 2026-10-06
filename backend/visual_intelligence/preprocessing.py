"""Image preprocessing utilities for GyanDrishti Visual Intelligence Engine.

Provides optimized, deterministic computer-vision filters for whiteboard,
blackboard, and slide keyframes to enhance OCR accuracy without destroying
mathematical symbols.
"""

from typing import Dict, Tuple
import cv2
import numpy as np

from .schemas import PreprocessingVariant


class ImagePreprocessor:
    """Applies non-destructive image preprocessing filters to enhance text clarity."""

    def __init__(self, max_dimension: int = 1920) -> None:
        self.max_dimension = max_dimension

    def resize_if_needed(self, img: np.ndarray) -> np.ndarray:
        """Scales image proportionally if it exceeds maximum resolution limit."""
        h, w = img.shape[:2]
        if max(h, w) <= self.max_dimension:
            return img

        scale = self.max_dimension / float(max(h, w))
        new_w = int(w * scale)
        new_h = int(h * scale)
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    def to_grayscale(self, img: np.ndarray) -> np.ndarray:
        """Converts BGR or RGB image to single-channel 8-bit grayscale."""
        if len(img.shape) == 2:
            return img
        if img.shape[2] == 4:
            return cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def apply_clahe(
        self,
        gray: np.ndarray,
        clip_limit: float = 2.0,
        tile_grid_size: Tuple[int, int] = (8, 8),
    ) -> np.ndarray:
        """Applies Contrast Limited Adaptive Histogram Equalization (CLAHE)."""
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        return clahe.apply(gray)

    def denoise(self, gray: np.ndarray) -> np.ndarray:
        """Applies gentle edge-preserving bilateral filtering to reduce camera noise."""
        return cv2.bilateralFilter(gray, d=5, sigmaColor=50, sigmaSpace=50)

    def adaptive_threshold(self, gray: np.ndarray) -> np.ndarray:
        """Applies adaptive Gaussian thresholding for high-contrast binarization."""
        return cv2.adaptiveThreshold(
            gray,
            maxValue=255,
            adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            thresholdType=cv2.THRESH_BINARY,
            blockSize=15,
            C=8,
        )

    def detect_and_invert_blackboard(self, gray: np.ndarray) -> Tuple[np.ndarray, bool]:
        """Detects if frame is a dark blackboard (mean luminance < 100).

        If blackboard detected, returns inverted image (dark strokes on white background)
        which standard OCR engines parse with significantly higher precision.
        """
        mean_intensity = float(np.mean(gray))
        is_blackboard = mean_intensity < 100.0
        if is_blackboard:
            inverted = cv2.bitwise_not(gray)
            return inverted, True
        return gray, False

    def process(
        self,
        img: np.ndarray,
        variant: PreprocessingVariant = PreprocessingVariant.ORIGINAL,
    ) -> np.ndarray:
        """Executes a specific preprocessing pipeline variant."""
        resized = self.resize_if_needed(img)

        if variant == PreprocessingVariant.ORIGINAL:
            return resized

        gray = self.to_grayscale(resized)

        if variant == PreprocessingVariant.GRAYSCALE:
            return gray
        elif variant == PreprocessingVariant.CLAHE:
            return self.apply_clahe(gray)
        elif variant == PreprocessingVariant.ADAPTIVE_THRESHOLD:
            denoised = self.denoise(gray)
            return self.adaptive_threshold(denoised)
        elif variant == PreprocessingVariant.INVERTED_BLACKBOARD:
            inverted, _ = self.detect_and_invert_blackboard(gray)
            return inverted

        return resized

    def prepare_variants(self, img: np.ndarray) -> Dict[str, np.ndarray]:
        """Prepares standard set of preprocessed variants for multi-pass OCR."""
        resized = self.resize_if_needed(img)
        gray = self.to_grayscale(resized)
        clahe = self.apply_clahe(gray)
        inverted, is_blackboard = self.detect_and_invert_blackboard(gray)

        variants: Dict[str, np.ndarray] = {
            "original": resized,
            "grayscale": gray,
            "clahe": clahe,
        }
        if is_blackboard:
            variants["inverted_blackboard"] = inverted

        return variants
