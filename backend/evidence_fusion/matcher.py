"""Deterministic mathematical and conceptual matcher for evidence fusion.

Provides rule-based equation normalization and conflict detection without LLMs.
"""

import re
from typing import Dict, List, Optional, Set, Tuple


class DeterministicMathMatcher:
    """Normalizes and cross-references spoken mathematical phrases with OCR strings."""

    # Canonical physical variable dictionary
    VARIABLE_MAP = {
        "current": "I",
        "voltage": "V",
        "resistance": "R",
        "force": "F",
        "mass": "m",
        "acceleration": "a",
        "energy": "E",
        "power": "P",
        "velocity": "v",
        "speed of light": "c",
    }

    # Common spoken phrase templates -> canonical formulas
    SPOKEN_PATTERNS = [
        # current = voltage / resistance
        (
            r"(?i)\bcurrent\s+(?:is\s+equal\s+to|equals|is)\s+voltage\s+divided\s+by\s+resistance\b",
            "I = V / R",
        ),
        (
            r"(?i)\bI\s+(?:is\s+equal\s+to|equals|is)\s+V\s+divided\s+by\s+R\b",
            "I = V / R",
        ),
        # voltage = current * resistance
        (
            r"(?i)\bvoltage\s+(?:is\s+equal\s+to|equals|is)\s+current\s+(?:times|multiplied\s+by|\*)\s+resistance\b",
            "V = I * R",
        ),
        (
            r"(?i)\bV\s+(?:is\s+equal\s+to|equals|is)\s+I\s+(?:times|multiplied\s+by|\*)\s+R\b",
            "V = I * R",
        ),
        # force = mass * acceleration
        (
            r"(?i)\bforce\s+(?:is\s+equal\s+to|equals|is)\s+mass\s+(?:times|multiplied\s+by|\*)\s+acceleration\b",
            "F = m * a",
        ),
        # energy = mass * c^2
        (
            r"(?i)\benergy\s+(?:is\s+equal\s+to|equals|is)\s+mass\s+(?:times|\*)\s+(?:c|speed of light)\s+(?:squared|\^2)\b",
            "E = m * c^2",
        ),
        # Conflicting phrases for verification: current = voltage * resistance
        (
            r"(?i)\bcurrent\s+(?:is\s+equal\s+to|equals|is)\s+voltage\s+(?:times|multiplied\s+by|\*)\s+resistance\b",
            "I = V * R",
        ),
        (
            r"(?i)\bI\s+(?:is\s+equal\s+to|equals|is)\s+V\s+(?:times|multiplied\s+by|\*)\s+R\b",
            "I = V * R",
        ),
    ]

    @classmethod
    def normalize_equation(cls, eq_str: str) -> str:
        """Standardizes equation string spacing and operators."""
        if not eq_str:
            return ""
        s = eq_str.strip()
        # Remove LaTeX escapes if present
        s = s.replace(r"\cdot", "*").replace(r"\times", "*")
        # Normalize multiplication
        s = re.sub(r"\s*[*x×]\s*", " * ", s)
        # Normalize division
        s = re.sub(r"\s*[/÷]\s*", " / ", s)
        # Normalize equality
        s = re.sub(r"\s*[=]\s*", " = ", s)
        # Standardize spaces around operators
        s = re.sub(r"\s*\+\s*", " + ", s)
        s = re.sub(r"\s*-\s*", " - ", s)
        # Clean extra spaces
        return re.sub(r"\s+", " ", s).strip()

    @classmethod
    def extract_math_from_speech(cls, text: str) -> Optional[str]:
        """Detects whether speech explicitly dictated a mathematical equation."""
        if not text:
            return None

        # Check spoken patterns
        for pattern, formula in cls.SPOKEN_PATTERNS:
            if re.search(pattern, text):
                return formula

        # Check direct formula utterances e.g. "I = V/R"
        direct_match = re.search(r"\b([A-Za-z])\s*=\s*([A-Za-z0-9_\s*+/^]+)\b", text)
        if direct_match:
            candidate = f"{direct_match.group(1)} = {direct_match.group(2)}"
            return cls.normalize_equation(candidate)

        return None

    @classmethod
    def compare_equations(
        cls, speech_eq: Optional[str], visual_eq: Optional[str]
    ) -> Tuple[bool, bool, str]:
        """Compares speech equation and visual OCR equation.

        Returns:
            (is_match, is_conflict, explanation)
        """
        if not speech_eq or not visual_eq:
            return False, False, "Missing speech or visual equation"

        norm_speech = cls.normalize_equation(speech_eq)
        norm_visual = cls.normalize_equation(visual_eq)

        # Exact match
        if norm_speech.lower() == norm_visual.lower():
            return True, False, "Exact equation equivalence"

        # Split LHS and RHS
        s_parts = norm_speech.split(" = ")
        v_parts = norm_visual.split(" = ")

        if len(s_parts) == 2 and len(v_parts) == 2:
            s_lhs, s_rhs = s_parts[0].strip().lower(), s_parts[1].strip().lower()
            v_lhs, v_rhs = v_parts[0].strip().lower(), v_parts[1].strip().lower()

            if s_lhs == v_lhs:
                # Same dependent variable (e.g. 'I')
                # Check if RHS operators conflict (e.g. '/' vs '*')
                s_has_div = "/" in s_rhs
                v_has_div = "/" in v_rhs
                s_has_mult = "*" in s_rhs
                v_has_mult = "*" in v_rhs

                if (s_has_div and v_has_mult) or (s_has_mult and v_has_div):
                    return (
                        False,
                        True,
                        f"Mathematical conflict: Speech states '{norm_speech}' but Visual displays '{norm_visual}'",
                    )

                if s_rhs.replace(" ", "") == v_rhs.replace(" ", ""):
                    return True, False, "Semantic RHS equivalence"

        return False, False, f"Different equations: '{norm_speech}' vs '{norm_visual}'"

    @classmethod
    def conceptual_domain_match(cls, speech_text: str, visual_text: str) -> bool:
        """Determines if speech and visual evidence share the same conceptual domain."""
        s = speech_text.lower()
        v = visual_text.lower()

        # Ohm's Law domain
        ohm_terms = {
            "ohm", "current", "voltage", "resistance",
            "i = v / r", "i = v/r", "v = i * r", "v = i*r", "v/r", "i * r"
        }
        # Relativity domain
        relativity_terms = {"einstein", "relativity", "energy", "mass", "e = mc", "c^2", "e = m * c^2"}
        # Newton domain
        newton_terms = {"newton", "force", "acceleration", "f = ma", "f = m * a", "momentum"}

        def domain_count(text: str, domain: Set[str]) -> int:
            return sum(1 for term in domain if term in text)

        for domain in [ohm_terms, relativity_terms, newton_terms]:
            if domain_count(s, domain) > 0 and domain_count(v, domain) > 0:
                return True

        return False
