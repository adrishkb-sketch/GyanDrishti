"""GyanDrishti Canonical Lecture Memory Engine (Milestone 5).

Provides immutable, evidence-grounded lecture memory persistence with
strict provenance, local atomic storage, and frontend compatibility.
"""

from .builder import LectureMemoryBuilder
from .provenance import (
    Provenance,
    create_derived_provenance,
    create_multimodal_provenance,
    create_speech_provenance,
    create_visual_provenance,
)
from .schemas import (
    LectureMemory,
    LectureMetadata,
    MemoryConcept,
    MemoryDefinition,
    MemoryEquation,
    MemoryImportantPoint,
    MemoryQuestionCandidate,
    MemoryTimelineEvent,
    MemoryVisualReference,
)
from .serializers import to_frontend_dict, to_markdown_notes
from .storage import (
    CorruptMemoryError,
    InvalidSessionIdError,
    LectureMemoryStorage,
    LectureMemoryStorageError,
    MemoryNotFoundError,
)

__all__ = [
    "LectureMemory",
    "LectureMetadata",
    "MemoryConcept",
    "MemoryDefinition",
    "MemoryEquation",
    "MemoryImportantPoint",
    "MemoryQuestionCandidate",
    "MemoryTimelineEvent",
    "MemoryVisualReference",
    "Provenance",
    "create_speech_provenance",
    "create_visual_provenance",
    "create_multimodal_provenance",
    "create_derived_provenance",
    "LectureMemoryBuilder",
    "LectureMemoryStorage",
    "LectureMemoryStorageError",
    "MemoryNotFoundError",
    "CorruptMemoryError",
    "InvalidSessionIdError",
    "to_frontend_dict",
    "to_markdown_notes",
]
