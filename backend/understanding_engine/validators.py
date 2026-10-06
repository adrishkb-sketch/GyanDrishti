"""Output validation and JSON parsing module for GyanDrishti Understanding Engine.

Safely handles malformed LLM responses, Markdown codeblock wrappers, missing fields,
and schema validation errors without crashing the pipeline.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from .schemas import (
    Concept,
    Definition,
    Equation,
    ImportantPoint,
    LectureUnderstanding,
    QuestionCandidate,
    VisualReference,
)

logger = logging.getLogger(__name__)


class UnderstandingValidationError(Exception):
    """Raised when an LLM response cannot be parsed into valid understanding data."""
    pass


def extract_json_from_llm_text(text: str) -> Dict[str, Any]:
    """Extracts and parses JSON object from raw LLM output text.

    Handles:
    - Markdown code fences (```json ... ``` or ``` ... ```)
    - Surrounding conversational preamble or trailer text
    - Direct JSON string
    """
    cleaned = text.strip()
    if not cleaned:
        raise UnderstandingValidationError("Empty output received from LLM")

    # 1. Check for markdown code blocks
    codeblock_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    if codeblock_match:
        json_candidate = codeblock_match.group(1).strip()
        try:
            return json.loads(json_candidate)
        except json.JSONDecodeError:
            pass

    # 2. Try direct json.loads
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 3. Find outermost curly braces { ... }
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        substring = cleaned[first_brace : last_brace + 1]
        try:
            return json.loads(substring)
        except json.JSONDecodeError as e:
            raise UnderstandingValidationError(f"Malformed JSON in LLM response: {e}") from e

    raise UnderstandingValidationError("No JSON object could be extracted from LLM response")


def validate_and_build_understanding(
    raw_dict: Dict[str, Any],
    fallback_start: float,
    fallback_end: float,
    lecture_id: Optional[str] = None,
    raw_transcript_ref: Optional[str] = None,
    model_name: Optional[str] = None,
) -> LectureUnderstanding:
    """Validates raw dictionary into strongly typed LectureUnderstanding schema.

    Gracefully handles missing or partial fields without fabricating facts.
    """
    time_start = float(raw_dict.get("time_start", fallback_start))
    time_end = float(raw_dict.get("time_end", fallback_end))
    topic = str(raw_dict.get("topic", "Lecture Segment")).strip() or "Lecture Segment"
    confidence = float(raw_dict.get("confidence", 1.0))

    # Parse and validate concepts
    concepts: List[Concept] = []
    for item in raw_dict.get("concepts", []):
        if isinstance(item, dict) and (item.get("name") or item.get("explanation")):
            try:
                concepts.append(
                    Concept(
                        name=str(item.get("name", "Unnamed Concept")),
                        explanation=str(item.get("explanation", "")),
                        timestamp_start=float(item.get("timestamp_start", time_start)),
                        timestamp_end=float(item.get("timestamp_end", time_end)),
                    )
                )
            except (ValidationError, ValueError, TypeError) as e:
                logger.warning("Skipping invalid concept item: %s (%s)", item, e)

    # Parse and validate definitions
    definitions: List[Definition] = []
    for item in raw_dict.get("definitions", []):
        if isinstance(item, dict) and (item.get("term") or item.get("definition")):
            try:
                definitions.append(
                    Definition(
                        term=str(item.get("term", "")),
                        definition=str(item.get("definition", "")),
                        timestamp=float(item.get("timestamp", time_start)),
                    )
                )
            except (ValidationError, ValueError, TypeError) as e:
                logger.warning("Skipping invalid definition item: %s (%s)", item, e)

    # Parse and validate equations (strict: only if latex_or_text is present)
    equations: List[Equation] = []
    for item in raw_dict.get("equations", []):
        if isinstance(item, dict) and item.get("latex_or_text"):
            try:
                equations.append(
                    Equation(
                        latex_or_text=str(item.get("latex_or_text")),
                        description=str(item.get("description", "")),
                        timestamp=float(item.get("timestamp", time_start)),
                        explicitly_spoken=bool(item.get("explicitly_spoken", True)),
                    )
                )
            except (ValidationError, ValueError, TypeError) as e:
                logger.warning("Skipping invalid equation item: %s (%s)", item, e)

    # Parse and validate important points
    important_points: List[ImportantPoint] = []
    for item in raw_dict.get("important_points", []):
        if isinstance(item, dict) and item.get("point"):
            try:
                important_points.append(
                    ImportantPoint(
                        point=str(item.get("point", "")),
                        timestamp_start=float(item.get("timestamp_start", time_start)),
                        timestamp_end=float(item.get("timestamp_end", time_end)),
                        importance=str(item.get("importance", "high")),
                    )
                )
            except (ValidationError, ValueError, TypeError) as e:
                logger.warning("Skipping invalid important point item: %s (%s)", item, e)

    # Parse and validate visual references
    visual_refs: List[VisualReference] = []
    for item in raw_dict.get("visual_references", []):
        if isinstance(item, dict):
            try:
                visual_refs.append(
                    VisualReference(
                        timestamp=float(item.get("timestamp", time_start)),
                        source=str(item.get("source", "camera")),
                        event_type=str(item.get("event_type", "keyframe")),
                        frame_path=item.get("frame_path"),
                        relevance=str(item.get("relevance", "Associated visual evidence")),
                    )
                )
            except (ValidationError, ValueError, TypeError) as e:
                logger.warning("Skipping invalid visual reference item: %s (%s)", item, e)

    # Parse and validate question candidates
    questions: List[QuestionCandidate] = []
    for item in raw_dict.get("question_candidates", []):
        if isinstance(item, dict) and item.get("question"):
            try:
                questions.append(
                    QuestionCandidate(
                        question=str(item.get("question")),
                        expected_answer=item.get("expected_answer"),
                        difficulty=str(item.get("difficulty", "medium")),
                        relevant_timestamp=float(item.get("relevant_timestamp", time_start)),
                    )
                )
            except (ValidationError, ValueError, TypeError) as e:
                logger.warning("Skipping invalid question candidate item: %s (%s)", item, e)

    return LectureUnderstanding(
        lecture_id=lecture_id,
        time_start=time_start,
        time_end=time_end,
        topic=topic,
        concepts=concepts,
        definitions=definitions,
        equations=equations,
        important_points=important_points,
        visual_references=visual_refs,
        question_candidates=questions,
        confidence=confidence,
        raw_transcript_ref=raw_transcript_ref,
        model_name=model_name,
    )
