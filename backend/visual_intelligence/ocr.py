"""Optical Character Recognition (OCR) engines for GyanDrishti Visual Intelligence.

Provides a pluggable BaseOCREngine with:
1. RapidOCREngine: Local, offline ONNX-based OCR with Apple Silicon / Metal support
2. MockOCREngine: Deterministic, zero-dependency testing engine
3. detect_potential_math: Deterministic mathematical expression classifier
"""

from abc import ABC, abstractmethod
import re
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


def detect_potential_math(text: str) -> Tuple[bool, Optional[str]]:
    """Deterministically identifies whether an extracted text string contains mathematical equations.

    Rules:
    - Must contain equality or inequality operators (=, ≈, ≡, ≤, ≥, ≠)
    - Must contain variable letters or numbers on both sides of the operator
    - Checks for common formula patterns (e.g. 'I = V / R', 'E = mc^2', 'y = mx + b')
    - Does NOT call an LLM or invent mathematical symbols.
    """
    clean = text.strip()
    if not clean or len(clean) < 3:
        return False, None

    # Matches formula patterns: Variable [A-Za-z0-9_] = Expression [A-Za-z0-9_+\-*/\^() ]
    eq_patterns = [
        # Standard algebraic equations: LHS = RHS with operators or variables
        r"^[A-Za-z\u0370-\u03ff\u1f00-\u1fff][\w\s_]*[=≈≡≤≥≠][\w\s_+\-*/\^().\\]+$",
        # Fraction or ratio equations: e.g. I = V/R, a/b = c/d
        r"[\w]+\s*[=≈≡]\s*[\w\d]+\s*[/÷*+\-]\s*[\w\d]+",
        # Powers / exponents: e.g. E = mc^2, a^2 + b^2 = c^2
        r"[\w]+\s*[=≈≡]\s*[\w\d]+\s*[\^]\s*[\w\d]+",
        # Explicit math keywords + equality
        r"(?i)^(?:eq|formula|equation)\s*:\s*.+[=≈≡].+",
    ]

    for pat in eq_patterns:
        if re.search(pat, clean):
            return True, clean

    # Secondary check: has '=' or '≈' AND mathematical operator (+, -, *, /, ^) or numerical terms
    if any(op in clean for op in ["=", "≈", "≡", "≤", "≥"]):
        parts = re.split(r"[=≈≡≤≥]", clean, maxsplit=1)
        if len(parts) == 2:
            lhs = parts[0].strip()
            rhs = parts[1].strip()
            # Both LHS and RHS should contain alphanumeric identifiers and not be conversational text
            lhs_valid = bool(re.search(r"[A-Za-z0-9]", lhs))
            rhs_valid = bool(re.search(r"[A-Za-z0-9]", rhs))
            has_math_chars = bool(re.search(r"[\d+\-*/\^()_.]", rhs)) or bool(re.search(r"[\d+\-*/\^()_.]", lhs))
            # Exclude long conversational sentences that happen to contain '='
            if lhs_valid and rhs_valid and has_math_chars and len(clean.split()) <= 12:
                return True, clean

    return False, None


class BaseOCREngine(ABC):
    """Abstract interface for local offline OCR backends."""

    @abstractmethod
    def detect_and_recognize(
        self,
        img: np.ndarray,
    ) -> List[Tuple[List[List[float]], str, float]]:
        """Extracts text regions from input image array.

        Returns:
            List of (polygon_points, text_string, confidence_float)
            polygon_points format: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
        """
        pass


class RapidOCREngine(BaseOCREngine):
    """Local, offline OCR engine powered by rapidocr-onnxruntime.

    Uses compact ONNX models running on CPU/Metal with zero cloud or network dependencies.
    """

    def __init__(self, **kwargs: Any) -> None:
        self._engine: Optional[Any] = None
        self._init_kwargs = kwargs

    def _get_engine(self) -> Any:
        if self._engine is None:
            try:
                from rapidocr_onnxruntime import RapidOCR
                self._engine = RapidOCR(**self._init_kwargs)
            except ImportError as e:
                raise RuntimeError(
                    "rapidocr-onnxruntime is not installed. "
                    "Install with: pip install rapidocr-onnxruntime"
                ) from e
        return self._engine

    def detect_and_recognize(
        self,
        img: np.ndarray,
    ) -> List[Tuple[List[List[float]], str, float]]:
        """Processes image through RapidOCR ONNX pipeline."""
        engine = self._get_engine()
        results, _ = engine(img)

        if not results:
            return []

        parsed: List[Tuple[List[List[float]], str, float]] = []
        for item in results:
            # item format: [polygon_box, text_str, confidence_val]
            polygon = item[0]
            # Convert polygon numpy coordinates to plain float lists
            if hasattr(polygon, "tolist"):
                polygon_coords = polygon.tolist()
            else:
                polygon_coords = [[float(p[0]), float(p[1])] for p in polygon]

            text = str(item[1]).strip()
            confidence = float(item[2])
            # Clamp confidence to [0.0, 1.0]
            confidence = max(0.0, min(1.0, confidence))

            if text:
                parsed.append((polygon_coords, text, confidence))

        return parsed


class MockOCREngine(BaseOCREngine):
    """Deterministic mock OCR engine for fast, isolated unit testing."""

    def __init__(
        self,
        canned_results: Optional[List[Tuple[List[List[float]], str, float]]] = None,
        should_fail: bool = False,
    ) -> None:
        self.canned_results = canned_results or []
        self.should_fail = should_fail
        self.call_count = 0

    def detect_and_recognize(
        self,
        img: np.ndarray,
    ) -> List[Tuple[List[List[float]], str, float]]:
        self.call_count += 1
        if self.should_fail:
            raise RuntimeError("Simulated OCR engine hardware/runtime failure")
        return list(self.canned_results)
