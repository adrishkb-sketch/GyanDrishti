"""GyanDrishti Local Visual Reasoning & Diagram Understanding Engine.

Provides offline, open-weight VLM reasoning for classroom diagrams, graphs,
schematics, and board structure without mutating raw OCR evidence.
"""

from .schemas import (
    DiagramType,
    VLMValidationStatus,
    VisualReasoningProposal,
    VisualReasoningResult,
)
from .provider import BaseVLMProvider, MockVLMProvider
from .ollama_provider import OllamaVLMProvider
from .prompts import VLM_DIAGRAM_ANALYSIS_PROMPT, build_vlm_prompt
from .validators import VisualReasoningValidator
from .analyzer import VisualReasoningAnalyzer

__all__ = [
    "DiagramType",
    "VLMValidationStatus",
    "VisualReasoningProposal",
    "VisualReasoningResult",
    "BaseVLMProvider",
    "MockVLMProvider",
    "OllamaVLMProvider",
    "VLM_DIAGRAM_ANALYSIS_PROMPT",
    "build_vlm_prompt",
    "VisualReasoningValidator",
    "VisualReasoningAnalyzer",
]
