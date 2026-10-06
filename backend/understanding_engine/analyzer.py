"""High-level analyzer module for GyanDrishti Understanding Engine.

Coordinates prompt assembly, local LLM inference, schema validation, and error recovery
to extract structured pedagogical understanding from temporal lecture blocks.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union

from .llm import (
    BaseLLMProvider,
    LLMError,
    LLMTimeoutError,
    LLMUnavailableError,
    MockLLMProvider,
    OllamaProvider,
)
from .prompts import SYSTEM_UNDERSTANDING_PROMPT, format_synchronized_block_prompt
from .schemas import (
    LectureUnderstanding,
    VisualReference,
)
from .validators import (
    UnderstandingValidationError,
    extract_json_from_llm_text,
    validate_and_build_understanding,
)

logger = logging.getLogger(__name__)


def _get_default_provider() -> BaseLLMProvider:
    """Returns the best available local LLM provider or MockLLMProvider as fallback."""
    ollama = OllamaProvider()
    if ollama.is_available():
        return ollama
    return MockLLMProvider()


class LectureUnderstandingEngine:
    """Orchestrates local pedagogical comprehension of synchronized multimodal lecture blocks."""

    def __init__(self, provider: Optional[BaseLLMProvider] = None) -> None:
        """Args:

        provider: Configured BaseLLMProvider instance. If None, auto-selects available local runtime.
        """
        self.provider = provider or _get_default_provider()

    def analyze_block(
        self,
        start_time: float,
        end_time: float,
        speech_segments: List[Dict[str, Any]],
        visual_events: List[Dict[str, Any]],
        lecture_id: Optional[str] = None,
    ) -> LectureUnderstanding:
        """Analyzes a single temporal block with raw speech segments and visual events.

        Preserves raw transcript text without modification.
        """
        # Concatenate raw source text reference
        raw_text_ref = " ".join(
            s.get("text", "").strip() for s in speech_segments if s.get("text")
        ).strip()

        # Handle empty speech case without invoking LLM
        if not raw_text_ref:
            visual_refs = [
                VisualReference(
                    timestamp=float(v.get("timestamp", start_time)),
                    source=str(v.get("source", "camera")),
                    event_type=str(v.get("type", "keyframe")),
                    frame_path=v.get("frame_path"),
                    relevance="Visual activity observed during silent interval.",
                )
                for v in visual_events
            ]
            return LectureUnderstanding(
                lecture_id=lecture_id,
                time_start=start_time,
                time_end=end_time,
                topic="Silent Interval / Visual Demonstration",
                concepts=[],
                definitions=[],
                equations=[],
                important_points=[],
                visual_references=visual_refs,
                question_candidates=[],
                confidence=1.0,
                raw_transcript_ref="",
                model_name=self.provider.get_model_name(),
            )

        # Assemble prompt
        prompt = format_synchronized_block_prompt(
            start_time=start_time,
            end_time=end_time,
            speech_segments=speech_segments,
            visual_events=visual_events,
            lecture_id=lecture_id,
        )

        # Execute local LLM generation with graceful error recovery
        try:
            raw_response = self.provider.generate(
                prompt=prompt,
                system_prompt=SYSTEM_UNDERSTANDING_PROMPT,
                temperature=0.1,
            )
            raw_dict = extract_json_from_llm_text(raw_response)
            return validate_and_build_understanding(
                raw_dict=raw_dict,
                fallback_start=start_time,
                fallback_end=end_time,
                lecture_id=lecture_id,
                raw_transcript_ref=raw_text_ref,
                model_name=self.provider.get_model_name(),
            )

        except (LLMUnavailableError, LLMTimeoutError) as e:
            logger.error("LLM runtime error during understanding extraction: %s", e)
            # Safe fallback: preserve time bounds and transcript without crashing
            return LectureUnderstanding(
                lecture_id=lecture_id,
                time_start=start_time,
                time_end=end_time,
                topic="Understanding Unavailable (Runtime Offline)",
                concepts=[],
                definitions=[],
                equations=[],
                important_points=[],
                visual_references=[],
                question_candidates=[],
                confidence=0.0,
                raw_transcript_ref=raw_text_ref,
                model_name=self.provider.get_model_name(),
            )

        except (UnderstandingValidationError, Exception) as e:
            logger.error("Validation error parsing LLM response: %s", e)
            return LectureUnderstanding(
                lecture_id=lecture_id,
                time_start=start_time,
                time_end=end_time,
                topic="Understanding Incomplete (Parse Error)",
                concepts=[],
                definitions=[],
                equations=[],
                important_points=[],
                visual_references=[],
                question_candidates=[],
                confidence=0.0,
                raw_transcript_ref=raw_text_ref,
                model_name=self.provider.get_model_name(),
            )

    def analyze_synchronized_event(
        self,
        event: Any,
        lecture_id: Optional[str] = None,
    ) -> LectureUnderstanding:
        """Analyzes a SynchronizedEvent domain model from the temporal fusion engine."""
        speech_dicts = [
            s.model_dump() if hasattr(s, "model_dump") else s
            for s in getattr(event, "speech", [])
        ]
        visual_dicts = [
            v.model_dump() if hasattr(v, "model_dump") else v
            for v in getattr(event, "visual_events", [])
        ]
        return self.analyze_block(
            start_time=getattr(event, "start", 0.0),
            end_time=getattr(event, "end", 0.0),
            speech_segments=speech_dicts,
            visual_events=visual_dicts,
            lecture_id=lecture_id,
        )

    def analyze_timeline(self, timeline: Any) -> List[LectureUnderstanding]:
        """Processes all synchronized blocks within a unified LectureTimeline."""
        lecture_id = getattr(timeline, "lecture_id", None)
        sync_events = getattr(timeline, "synchronized_events", [])
        results: List[LectureUnderstanding] = []

        for se in sync_events:
            understanding = self.analyze_synchronized_event(se, lecture_id=lecture_id)
            results.append(understanding)

        return results
