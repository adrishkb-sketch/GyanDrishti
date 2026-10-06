"""Visual Reasoning Analyzer coordinating VLM inference and deterministic validation."""

import os
import time
from typing import Any, List, Optional
from .prompts import build_vlm_prompt
from .provider import BaseVLMProvider, MockVLMProvider
from .schemas import (
    DiagramType,
    VLMValidationStatus,
    VisualReasoningProposal,
    VisualReasoningResult,
)
from .validators import VisualReasoningValidator


class VisualReasoningAnalyzer:
    """Orchestrates local VLM diagram analysis with evidence grounding."""

    def __init__(
        self,
        provider: Optional[BaseVLMProvider] = None,
        validator: Optional[VisualReasoningValidator] = None,
    ) -> None:
        self.provider = provider or MockVLMProvider()
        self.validator = validator or VisualReasoningValidator()

    def analyze_keyframe(
        self,
        image_path: str,
        keyframe_id: str,
        timestamp: float,
        session_id: Optional[str] = None,
        raw_ocr_text: Optional[str] = None,
        ocr_equations: Optional[List[str]] = None,
        subject_hint: str = "Engineering",
        is_empty_image: bool = False,
    ) -> VisualReasoningResult:
        """Executes VLM reasoning on a keyframe and validates the proposal against OCR evidence."""
        t0 = time.perf_counter()
        result_id = f"vr_{keyframe_id}"

        if is_empty_image:
            return VisualReasoningResult(
                id=result_id,
                session_id=session_id,
                keyframe_id=keyframe_id,
                timestamp=round(float(timestamp), 2),
                frame_path=image_path,
                raw_ocr_text=raw_ocr_text,
                proposal=None,
                validation_status=VLMValidationStatus.EMPTY_IMAGE,
                conflict_notes="Image has no visual diagram features.",
                latency_ms=round((time.perf_counter() - t0) * 1000.0, 2),
            )

        prompt = build_vlm_prompt(subject_hint=subject_hint)

        try:
            proposal = self.provider.generate_visual_proposal(
                image_path=image_path,
                prompt=prompt,
                ocr_context=raw_ocr_text,
            )
        except Exception as e:
            return VisualReasoningResult(
                id=result_id,
                session_id=session_id,
                keyframe_id=keyframe_id,
                timestamp=round(float(timestamp), 2),
                frame_path=image_path,
                raw_ocr_text=raw_ocr_text,
                proposal=None,
                validation_status=VLMValidationStatus.REJECTED,
                conflict_notes=f"VLM provider execution failure: {str(e)}",
                latency_ms=round((time.perf_counter() - t0) * 1000.0, 2),
            )

        status, conflict_notes = self.validator.validate_proposal(
            proposal=proposal,
            raw_ocr_text=raw_ocr_text,
            ocr_equations=ocr_equations,
            is_empty_image=is_empty_image,
        )

        latency = round((time.perf_counter() - t0) * 1000.0, 2)

        return VisualReasoningResult(
            id=result_id,
            session_id=session_id,
            keyframe_id=keyframe_id,
            timestamp=round(float(timestamp), 2),
            frame_path=image_path,
            raw_ocr_text=raw_ocr_text,
            proposal=proposal,
            validation_status=status,
            conflict_notes=conflict_notes,
            latency_ms=latency,
        )
