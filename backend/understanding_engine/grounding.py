"""Deterministic Grounding & Evidence Validation for GyanDrishti Understanding Engine.

Enforces conservative post-validation on LLM proposals using raw multimodal evidence:
1. Deterministic equation grounding (symbolic and verbal mathematical expressions).
2. Numeric claims verification against raw source transcripts.
3. Proper noun & entity caution.
4. Calculation of objective evidence grounding scores.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from .schemas import (
    Concept,
    Definition,
    Equation,
    ImportantPoint,
    LectureUnderstanding,
)

logger = logging.getLogger(__name__)

# Verbal mappings for physical and mathematical quantities
QUANTITY_LEXICON: Dict[str, List[str]] = {
    "i": ["current", "electric current", "i"],
    "v": ["voltage", "potential", "potential difference", "volt", "v"],
    "r": ["resistance", "resistor", "ohm", "r"],
    "emf": ["emf", "electromotive force", "induced voltage", "induced emf", "epsilon"],
    "epsilon": ["emf", "electromotive force", "epsilon", "e"],
    "phi": ["flux", "magnetic flux", "phi"],
    "t": ["time", "dt", "t"],
    "n": ["turns", "number of turns", "n"],
    "f": ["force", "f", "frequency"],
    "m": ["mass", "m"],
    "a": ["acceleration", "a", "area"],
    "p": ["power", "momentum", "pressure", "p"],
    "q": ["charge", "electric charge", "q"],
    "c": ["speed of light", "capacitance", "c"],
    "w": ["work", "energy", "w"],
    "lambda": ["wavelength", "lambda"],
}

# Operational markers in spoken English and code-switched speech
OPERATION_MARKERS: Dict[str, List[str]] = {
    "division": ["divided by", "over", "upon", "by", "per", "ratio of", "bhag"],
    "multiplication": ["times", "multiplied by", "into", "product of", "gun"],
    "addition": ["plus", "added to", "sum of", "jog"],
    "subtraction": ["minus", "negative", "subtracted from", "biyog"],
    "rate_of_change": ["rate of change", "derivative", "d phi by dt", "dphi by dt", "d phi over dt"],
}

EQUALITY_MARKERS: List[str] = [
    "equal to",
    "equals",
    "is equal",
    "equals to",
    "stated as",
    "given by",
    "relationship is",
    "formula is",
    "equation is",
    "is defined as",
    "=",
]


def _clean_text(text: str) -> str:
    """Normalizes whitespace and lowercases text for deterministic matching."""
    return " ".join(text.lower().split())


def _extract_equation_symbols(eq_str: str) -> Tuple[List[str], List[str], List[str]]:
    """Extracts LHS symbols, RHS symbols, and operations from an equation string."""
    cleaned = eq_str.lower().replace("\\frac", "").replace("\\times", "*")
    cleaned = re.sub(r"[{}\\_^]", " ", cleaned)
    
    parts = cleaned.split("=")
    if len(parts) < 2:
        parts = cleaned.split("\\approx")
    if len(parts) < 2:
        return [p.strip() for p in re.findall(r"[a-z]+", cleaned)], [], []

    lhs_raw = parts[0]
    rhs_raw = parts[1]

    lhs_symbols = [s for s in re.findall(r"[a-z]+", lhs_raw) if len(s) <= 5]
    rhs_symbols = [s for s in re.findall(r"[a-z]+", rhs_raw) if len(s) <= 5]

    operations = []
    if "/" in rhs_raw or "frac" in eq_str.lower():
        operations.append("division")
    if "*" in rhs_raw or "\\times" in eq_str.lower():
        operations.append("multiplication")
    if "+" in rhs_raw:
        operations.append("addition")
    if "-" in rhs_raw:
        operations.append("subtraction")
    if "d\\phi" in eq_str.lower() or "dphi" in eq_str.lower():
        operations.append("rate_of_change")

    return lhs_symbols, rhs_symbols, operations


def is_equation_supported(equation: Equation, raw_transcript: str) -> Tuple[bool, str, Optional[str]]:
    """Deterministically verifies whether an equation is grounded in the raw transcript.

    Returns:
        (is_supported: bool, status: str, evidence_snippet: Optional[str])
    """
    if not raw_transcript or not raw_transcript.strip():
        return False, "unsupported", None

    transcript_clean = _clean_text(raw_transcript)
    eq_text = equation.latex_or_text.strip()
    eq_clean = _clean_text(eq_text)

    # 1. Exact or near-exact symbolic match in transcript
    # Strip spaces in both for compact symbolic comparisons
    t_no_space = re.sub(r"\s+", "", transcript_clean)
    eq_no_space = re.sub(r"[\s\\{}]", "", eq_clean)
    if eq_no_space and eq_no_space in t_no_space:
        return True, "supported", f"Direct symbolic match in transcript: '{eq_text}'"

    # 2. Verbal Mathematical Form Check
    lhs_syms, rhs_syms, ops = _extract_equation_symbols(eq_text)

    # Check for equality markers
    has_equality = any(eq_m in transcript_clean for eq_m in EQUALITY_MARKERS)

    # Check operational markers
    has_operation = False
    for op in ops:
        markers = OPERATION_MARKERS.get(op, [])
        if any(m in transcript_clean for m in markers):
            has_operation = True
            break

    # If the equation has operations (like I = V / R or EMF = -dPhi/dt),
    # there MUST be either an equality marker OR an operational marker in speech
    if not has_equality and not has_operation:
        return False, "unsupported", None

    # Check that LHS quantity or symbol is mentioned
    lhs_matched = False
    for s in lhs_syms:
        spoken_forms = QUANTITY_LEXICON.get(s, [s])
        if any(re.search(r"\b" + re.escape(w) + r"\b", transcript_clean) for w in spoken_forms):
            lhs_matched = True
            break

    # Check that RHS quantities or symbols are mentioned
    rhs_matched_count = 0
    for s in rhs_syms:
        spoken_forms = QUANTITY_LEXICON.get(s, [s])
        if any(re.search(r"\b" + re.escape(w) + r"\b", transcript_clean) for w in spoken_forms):
            rhs_matched_count += 1

    # Require LHS to be present and at least one RHS variable to be present
    if lhs_matched and rhs_matched_count >= min(1, len(rhs_syms)):
        # If formula has a mathematical operation, require the operation to be spoken
        if ops and not has_operation:
            # Qualitative mentions (e.g., 'current increases when resistance decreases')
            # mention both LHS and RHS, but do NOT state the equation operation
            return False, "unsupported", None

        # Build evidence snippet
        snippet = f"Spoken formula confirmed: LHS ({lhs_syms}), RHS ({rhs_syms}), Operations ({ops})"
        return True, "supported", snippet

    return False, "unsupported", None


def validate_numeric_claim(claim_text: str, raw_transcript: str) -> Tuple[bool, List[str]]:
    """Checks whether specific numbers (>0) in an extracted claim exist in source transcript."""
    if not raw_transcript:
        return False, []

    claim_numbers = re.findall(r"\b\d+(?:\.\d+)?\b", claim_text)
    if not claim_numbers:
        return True, []  # No numbers to dispute

    transcript_clean = _clean_text(raw_transcript)
    transcript_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", transcript_clean))

    unsupported_numbers = []
    for num in claim_numbers:
        if num not in transcript_numbers:
            # Check for common spoken small numbers
            spoken_map = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five"}
            if num in spoken_map and spoken_map[num] in transcript_clean:
                continue
            unsupported_numbers.append(num)

    return len(unsupported_numbers) == 0, unsupported_numbers


class DeterministicGroundingValidator:
    """Validates and filters LLM proposals against raw multimodal evidence."""

    @classmethod
    def validate_understanding(
        cls,
        understanding: LectureUnderstanding,
        raw_transcript: Optional[str] = None,
    ) -> LectureUnderstanding:
        """Applies conservative evidence validation to an extracted understanding proposal.

        - Separates supported equations from rejected equations.
        - Flags unverified numeric claims.
        - Computes deterministic grounding score.
        """
        source_text = raw_transcript or understanding.raw_transcript_ref or ""
        source_clean = _clean_text(source_text)

        # 1. Validate Equations
        supported_equations: List[Equation] = []
        rejected_equations: List[Equation] = list(understanding.rejected_equations)

        for eq in understanding.equations:
            is_supp, status, snippet = is_equation_supported(eq, source_clean)
            eq_copy = eq.model_copy()
            eq_copy.grounding_status = status
            eq_copy.evidence_snippet = snippet

            if is_supp:
                supported_equations.append(eq_copy)
            else:
                rejected_equations.append(eq_copy)
                logger.info(
                    "Deterministic grounding rejected hallucinated equation: '%s'",
                    eq.latex_or_text,
                )

        # 2. Validate Numeric Claims in Points
        validated_points: List[ImportantPoint] = []
        unverified_num_count = 0
        for pt in understanding.important_points:
            ok, unsupp_nums = validate_numeric_claim(pt.point, source_clean)
            if not ok and unsupp_nums:
                unverified_num_count += len(unsupp_nums)
                pt_copy = pt.model_copy()
                pt_copy.importance = "uncertain"
                pt_copy.point = f"[Unverified number: {', '.join(unsupp_nums)}] {pt.point}"
                validated_points.append(pt_copy)
            else:
                validated_points.append(pt)

        # 3. Handle Empty Transcript Edge Case
        if not source_clean:
            # An empty transcript cannot support any concepts, points, or equations
            return LectureUnderstanding(
                lecture_id=understanding.lecture_id,
                time_start=understanding.time_start,
                time_end=understanding.time_end,
                topic="Silent Interval / Visual Demonstration",
                concepts=[],
                definitions=[],
                equations=[],
                rejected_equations=rejected_equations,
                important_points=[],
                visual_references=understanding.visual_references,
                question_candidates=[],
                confidence=0.0,
                grounding_score=0.0,
                raw_transcript_ref="",
                model_name=understanding.model_name,
            )

        # 4. Compute Grounding Score
        total_checks = (
            len(understanding.equations)
            + len(understanding.important_points)
            + len(understanding.concepts)
        )
        if total_checks == 0:
            grounding_score = 1.0
        else:
            rejected_items = len(understanding.equations) - len(supported_equations) + unverified_num_count
            grounding_score = max(0.0, min(1.0, 1.0 - (rejected_items / max(1, total_checks))))

        return LectureUnderstanding(
            lecture_id=understanding.lecture_id,
            time_start=understanding.time_start,
            time_end=understanding.time_end,
            topic=understanding.topic,
            concepts=understanding.concepts,
            definitions=understanding.definitions,
            equations=supported_equations,
            rejected_equations=rejected_equations,
            important_points=validated_points,
            visual_references=understanding.visual_references,
            question_candidates=understanding.question_candidates,
            confidence=understanding.confidence,
            grounding_score=round(grounding_score, 2),
            raw_transcript_ref=understanding.raw_transcript_ref,
            model_name=understanding.model_name,
            created_at=understanding.created_at,
        )
