"""GyanDrishti Lecture Understanding Engine (Milestone 4).

Transforms synchronized multimodal speech and visual streams into structured
pedagogical concepts, definitions, equations, takeaways, and revision questions
without mutating raw source transcripts.
"""

from .analyzer import LectureUnderstandingEngine
from .llm import (
    BaseLLMProvider,
    LLMError,
    LLMTimeoutError,
    LLMUnavailableError,
    LocalHTTPProvider,
    MockLLMProvider,
    OllamaProvider,
)
from .prompts import SYSTEM_UNDERSTANDING_PROMPT, format_synchronized_block_prompt
from .schemas import (
    Concept,
    Definition,
    Equation,
    ImportantPoint,
    LectureUnderstanding,
    QuestionCandidate,
    VisualReference,
)
from .validators import (
    UnderstandingValidationError,
    extract_json_from_llm_text,
    validate_and_build_understanding,
)

__all__ = [
    "BaseLLMProvider",
    "Concept",
    "Definition",
    "Equation",
    "ImportantPoint",
    "LLMError",
    "LLMTimeoutError",
    "LLMUnavailableError",
    "LectureUnderstanding",
    "LectureUnderstandingEngine",
    "LocalHTTPProvider",
    "MockLLMProvider",
    "OllamaProvider",
    "QuestionCandidate",
    "SYSTEM_UNDERSTANDING_PROMPT",
    "UnderstandingValidationError",
    "VisualReference",
    "extract_json_from_llm_text",
    "format_synchronized_block_prompt",
    "validate_and_build_understanding",
]
