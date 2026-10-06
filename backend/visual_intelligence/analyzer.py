"""Core analyzer for GyanDrishti Visual Intelligence Engine.

Coordinates image preprocessing, OCR execution, spatial bounding box calculation,
mathematical expression filtering, and result aggregation into VisualAnalysisResult.
"""

import os
import time
from typing import Any, Dict, List, Optional, Union
import cv2
import numpy as np

from .ocr import BaseOCREngine, RapidOCREngine, detect_potential_math
from .preprocessing import ImagePreprocessor
from .schemas import (
    BoundingBox,
    OCRStatus,
    PreprocessingVariant,
    VisualAnalysisResult,
    VisualTextEvidence,
)


class VisualIntelligenceAnalyzer:
    """Analyzes lecture keyframes to extract textual and mathematical evidence."""

    def __init__(
        self,
        ocr_engine: Optional[BaseOCREngine] = None,
        preprocessor: Optional[ImagePreprocessor] = None,
        uncertain_confidence_threshold: float = 0.45,
    ) -> None:
        self.ocr_engine = ocr_engine or RapidOCREngine()
        self.preprocessor = preprocessor or ImagePreprocessor()
        self.uncertain_threshold = uncertain_confidence_threshold

    def analyze_image(
        self,
        image_input: Union[str, np.ndarray],
        keyframe_id: str,
        timestamp: float,
        session_id: Optional[str] = None,
        variant: PreprocessingVariant = PreprocessingVariant.ORIGINAL,
    ) -> VisualAnalysisResult:
        """Processes a single image file or in-memory numpy array.

        Returns a strongly-typed VisualAnalysisResult preserving all raw evidence.
        """
        start_time = time.perf_counter()
        warnings: List[str] = []

        # 1. Load Image
        if isinstance(image_input, str):
            image_path = image_input
            if not os.path.exists(image_path):
                return VisualAnalysisResult(
                    keyframe_id=keyframe_id,
                    timestamp=round(float(timestamp), 2),
                    source_image=image_path,
                    processing_status=OCRStatus.IMAGE_NOT_FOUND,
                    warnings=[f"Image file does not exist on disk: {image_path}"],
                    latency_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
                )
            img = cv2.imread(image_path)
            if img is None:
                return VisualAnalysisResult(
                    keyframe_id=keyframe_id,
                    timestamp=round(float(timestamp), 2),
                    source_image=image_path,
                    processing_status=OCRStatus.FAILED,
                    warnings=[f"Failed to decode image from disk: {image_path}"],
                    latency_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
                )
        elif isinstance(image_input, np.ndarray):
            image_path = f"memory://{keyframe_id}"
            img = image_input
        else:
            return VisualAnalysisResult(
                keyframe_id=keyframe_id,
                timestamp=round(float(timestamp), 2),
                source_image="unknown",
                processing_status=OCRStatus.FAILED,
                warnings=["Unsupported image input type; must be filepath or np.ndarray"],
                latency_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
            )

        h, w = img.shape[:2]
        dims = {"width": w, "height": h}

        # 2. Preprocessing
        try:
            # Check for blackboard writing (dark background)
            gray = self.preprocessor.to_grayscale(img)
            _, is_blackboard = self.preprocessor.detect_and_invert_blackboard(gray)

            if is_blackboard and variant == PreprocessingVariant.ORIGINAL:
                processed_img = self.preprocessor.process(
                    img, variant=PreprocessingVariant.INVERTED_BLACKBOARD
                )
                used_variant = "inverted_blackboard"
            else:
                processed_img = self.preprocessor.process(img, variant=variant)
                used_variant = variant.value
        except Exception as e:
            warnings.append(f"Preprocessing warning: {str(e)}")
            processed_img = img
            used_variant = "original"

        # 3. Optical Character Recognition
        try:
            raw_detections = self.ocr_engine.detect_and_recognize(processed_img)
        except Exception as e:
            return VisualAnalysisResult(
                keyframe_id=keyframe_id,
                timestamp=round(float(timestamp), 2),
                source_image=image_path,
                processing_status=OCRStatus.FAILED,
                warnings=[f"OCR engine failure: {str(e)}"],
                latency_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
                image_dimensions=dims,
            )

        # 4. Handle Empty Extraction
        if not raw_detections:
            return VisualAnalysisResult(
                keyframe_id=keyframe_id,
                timestamp=round(float(timestamp), 2),
                source_image=image_path,
                extracted_text=[],
                raw_text_combined="",
                overall_confidence=0.0,
                processing_status=OCRStatus.NO_TEXT_DETECTED,
                potential_equations=[],
                warnings=warnings,
                latency_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
                image_dimensions=dims,
            )

        # 5. Build Structured Evidence Items
        text_items: List[VisualTextEvidence] = []
        confidences: List[float] = []
        potential_equations: List[str] = []
        text_lines: List[str] = []

        for idx, (polygon, text_str, conf) in enumerate(raw_detections):
            text_str = text_str.strip()
            if not text_str:
                continue

            text_lines.append(text_str)
            confidences.append(conf)

            # Mathematical symbol check
            is_math, math_expr = detect_potential_math(text_str)
            if is_math and math_expr:
                potential_equations.append(math_expr)

            # Bounding box
            bbox = None
            if polygon and len(polygon) == 4:
                try:
                    bbox = BoundingBox.from_polygon(polygon)
                except Exception:
                    bbox = None

            evidence = VisualTextEvidence(
                id=f"{keyframe_id}_ocr_{idx+1:03d}",
                session_id=session_id,
                keyframe_id=keyframe_id,
                timestamp=round(float(timestamp), 2),
                text=text_str,
                confidence=conf,
                bounding_box=bbox,
                preprocessing_variant=used_variant,
                source_image=image_path,
                is_potential_math=is_math,
            )
            text_items.append(evidence)

        # Overall confidence
        mean_conf = sum(confidences) / len(confidences) if confidences else 0.0

        # Status
        status = OCRStatus.SUCCESS
        if mean_conf < self.uncertain_threshold:
            status = OCRStatus.UNCERTAIN

        combined_text = " ".join(text_lines)
        latency = round((time.perf_counter() - start_time) * 1000.0, 2)

        return VisualAnalysisResult(
            keyframe_id=keyframe_id,
            timestamp=round(float(timestamp), 2),
            source_image=image_path,
            extracted_text=text_items,
            raw_text_combined=combined_text,
            overall_confidence=round(mean_conf, 4),
            processing_status=status,
            potential_equations=potential_equations,
            warnings=warnings,
            latency_ms=latency,
            image_dimensions=dims,
        )

    def analyze_keyframes(
        self,
        keyframes: List[Any],
        session_id: Optional[str] = None,
    ) -> List[VisualAnalysisResult]:
        """Analyzes a sequence of VisualEvent or dict objects representing keyframes."""
        results: List[VisualAnalysisResult] = []
        for kf in keyframes:
            # Supports VisualEvent Pydantic model or plain dict
            if hasattr(kf, "frame_path"):
                frame_path = getattr(kf, "frame_path")
                ts = getattr(kf, "timestamp", 0.0)
                kf_id = os.path.splitext(os.path.basename(frame_path))[0]
            elif isinstance(kf, dict):
                frame_path = kf.get("frame_path", "")
                ts = kf.get("timestamp", 0.0)
                kf_id = kf.get("keyframe_id") or os.path.splitext(os.path.basename(frame_path))[0]
            else:
                continue

            result = self.analyze_image(
                image_input=frame_path,
                keyframe_id=kf_id,
                timestamp=ts,
                session_id=session_id,
            )
            results.append(result)

        return results
