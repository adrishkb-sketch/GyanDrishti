"""GyanDrishti Visual Intelligence Engine.

Provides offline, local OCR and board understanding for classroom whiteboards,
blackboards, slides, and screen recordings.
"""

from .schemas import (
    BoundingBox,
    OCRStatus,
    PreprocessingVariant,
    VisualTextEvidence,
    VisualAnalysisResult,
    MultimodalAssociation,
)
from .preprocessing import ImagePreprocessor
from .ocr import BaseOCREngine, RapidOCREngine, MockOCREngine, detect_potential_math
from .analyzer import VisualIntelligenceAnalyzer
from .association import TemporalVisualAssociator
from .storage import VisualEvidenceStorage

__all__ = [
    "BoundingBox",
    "OCRStatus",
    "PreprocessingVariant",
    "VisualTextEvidence",
    "VisualAnalysisResult",
    "MultimodalAssociation",
    "ImagePreprocessor",
    "BaseOCREngine",
    "RapidOCREngine",
    "MockOCREngine",
    "detect_potential_math",
    "VisualIntelligenceAnalyzer",
    "TemporalVisualAssociator",
    "VisualEvidenceStorage",
]
