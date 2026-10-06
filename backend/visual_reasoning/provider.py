"""Abstract interface and Mock provider for local Vision-Language Models."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from .schemas import DiagramType, VisualReasoningProposal


class BaseVLMProvider(ABC):
    """Abstract interface for local open-weight visual reasoning providers."""

    @abstractmethod
    def generate_visual_proposal(
        self,
        image_path: str,
        prompt: str,
        ocr_context: Optional[str] = None,
    ) -> VisualReasoningProposal:
        """Infers semantic understanding from an image without modifying OCR evidence."""
        pass


class MockVLMProvider(BaseVLMProvider):
    """Deterministic mock VLM provider for isolated testing and offline environments."""

    def __init__(
        self,
        default_proposal: Optional[VisualReasoningProposal] = None,
        should_fail: bool = False,
        malformed_json: bool = False,
    ) -> None:
        self.default_proposal = default_proposal or VisualReasoningProposal(
            model_name="mock-vlm-2b",
            model_version="q4_k_m",
            diagram_type=DiagramType.CIRCUIT_DIAGRAM,
            description="Electrical circuit containing DC battery and series resistor.",
            entities_detected=["Battery V1", "Resistor R1", "Ammeter A1"],
            relations_detected=["V1 connected to R1", "R1 in series with A1"],
            visible_equations=["I = V / R"],
            confidence=0.88,
            raw_response="{\"diagram_type\": \"circuit_diagram\"}",
        )
        self.should_fail = should_fail
        self.malformed_json = malformed_json
        self.invocation_count = 0

    def generate_visual_proposal(
        self,
        image_path: str,
        prompt: str,
        ocr_context: Optional[str] = None,
    ) -> VisualReasoningProposal:
        self.invocation_count += 1
        if self.should_fail:
            raise RuntimeError("Local VLM engine error: model out of memory or device unavailable")
        if self.malformed_json:
            return VisualReasoningProposal(
                model_name="mock-vlm-corrupt",
                description="Malformed output error",
                confidence=0.1,
                raw_response="Invalid { json text not closed",
            )
        return self.default_proposal
