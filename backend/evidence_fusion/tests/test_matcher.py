"""Tests for DeterministicMathMatcher."""

import pytest
from evidence_fusion.matcher import DeterministicMathMatcher


def test_normalize_equation():
    assert DeterministicMathMatcher.normalize_equation("I=V/R") == "I = V / R"
    assert DeterministicMathMatcher.normalize_equation("I  =   V / R") == "I = V / R"
    assert DeterministicMathMatcher.normalize_equation("V=I*R") == "V = I * R"
    assert DeterministicMathMatcher.normalize_equation("F = m x a") == "F = m * a"


def test_extract_math_from_speech():
    assert (
        DeterministicMathMatcher.extract_math_from_speech(
            "current is equal to voltage divided by resistance"
        )
        == "I = V / R"
    )
    assert (
        DeterministicMathMatcher.extract_math_from_speech("I equals V divided by R")
        == "I = V / R"
    )
    assert (
        DeterministicMathMatcher.extract_math_from_speech("voltage is current times resistance")
        == "V = I * R"
    )
    assert (
        DeterministicMathMatcher.extract_math_from_speech("force equals mass times acceleration")
        == "F = m * a"
    )
    assert (
        DeterministicMathMatcher.extract_math_from_speech("energy equals mass times c squared")
        == "E = m * c^2"
    )
    # Qualitative statement without formula
    assert (
        DeterministicMathMatcher.extract_math_from_speech(
            "current increases when resistance decreases"
        )
        is None
    )


def test_compare_equations_exact():
    is_match, is_conflict, reason = DeterministicMathMatcher.compare_equations(
        "I = V / R", "I = V/R"
    )
    assert is_match is True
    assert is_conflict is False


def test_compare_equations_conflict():
    is_match, is_conflict, reason = DeterministicMathMatcher.compare_equations(
        "I = V / R", "I = V * R"
    )
    assert is_match is False
    assert is_conflict is True
    assert "conflict" in reason.lower()


def test_conceptual_domain_match():
    assert DeterministicMathMatcher.conceptual_domain_match(
        "according to Ohm's law current flows", "Ohm's Law: I = V/R"
    ) is True
    # Unrelated domains
    assert DeterministicMathMatcher.conceptual_domain_match(
        "according to Ohm's law", "E = mc^2"
    ) is False
