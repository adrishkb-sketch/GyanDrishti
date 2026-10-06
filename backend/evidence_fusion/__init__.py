"""GyanDrishti Deterministic Multimodal Evidence Fusion Engine.

Combines speech evidence, visual OCR evidence, and temporal proximity into
auditable fused multimodal evidence without LLM hallucinations or ungrounded trust.
"""

from .schemas import (
    EvidenceSourceType,
    FusionState,
    FusedEvidenceItem,
    MultimodalFusionReport,
    SpeechEvidenceItem,
    VisualEvidenceItem,
)
from .matcher import DeterministicMathMatcher
from .policies import FusionPolicy
from .fusion import MultimodalEvidenceFusor
from .analyzer import FusionPipelineAnalyzer

__all__ = [
    "EvidenceSourceType",
    "FusionState",
    "SpeechEvidenceItem",
    "VisualEvidenceItem",
    "FusedEvidenceItem",
    "MultimodalFusionReport",
    "DeterministicMathMatcher",
    "FusionPolicy",
    "MultimodalEvidenceFusor",
    "FusionPipelineAnalyzer",
]
