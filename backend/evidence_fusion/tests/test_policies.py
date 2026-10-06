"""Tests for FusionPolicy rules including Cases 1 through 5."""

import pytest
from evidence_fusion.policies import FusionPolicy
from evidence_fusion.schemas import (
    FusionState,
    SpeechEvidenceItem,
    VisualEvidenceItem,
)


@pytest.fixture
def policy():
    return FusionPolicy(proximity_window_seconds=6.0, uncertainty_threshold=0.45)


def test_case_1_multimodal_supported(policy):
    """CASE 1: Speech states formula, visual displays exact formula -> multimodal_supported."""
    speech = SpeechEvidenceItem(
        speech_id="s1",
        timestamp_start=12.0,
        timestamp_end=16.0,
        text="current is equal to voltage divided by resistance",
        confidence=0.92,
    )
    visual = VisualEvidenceItem(
        keyframe_id="kf1",
        timestamp=14.0,
        frame_path="frames/kf1.jpg",
        raw_text="I = V / R",
        confidence=0.90,
        potential_equations=["I = V / R"],
    )

    state, conf, conflict, reason = policy.evaluate_fusion(speech, visual)
    assert state == FusionState.MULTIMODAL_SUPPORTED
    assert conf >= 0.90
    assert conflict is None
    assert "consensus" in reason.lower()


def test_case_2_qualitative_speech_visual_only(policy):
    """CASE 2: Speech explains qualitative relationship without formula, visual displays formula -> visual_only."""
    speech = SpeechEvidenceItem(
        speech_id="s2",
        timestamp_start=20.0,
        timestamp_end=24.0,
        text="current increases when resistance decreases in the circuit",
        confidence=0.91,
    )
    visual = VisualEvidenceItem(
        keyframe_id="kf2",
        timestamp=22.0,
        frame_path="frames/kf2.jpg",
        raw_text="Ohm's Law: I = V / R",
        confidence=0.88,
        potential_equations=["I = V / R"],
    )

    state, conf, conflict, reason = policy.evaluate_fusion(speech, visual)
    assert state == FusionState.VISUAL_ONLY
    assert conf == 0.88
    assert conflict is None
    assert "not spoken" in reason.lower()


def test_case_3_mathematical_conflict(policy):
    """CASE 3: Speech states I = V / R, Visual displays I = V * R -> conflict."""
    speech = SpeechEvidenceItem(
        speech_id="s3",
        timestamp_start=30.0,
        timestamp_end=34.0,
        text="I = V / R",
        confidence=0.95,
        detected_math="I = V / R",
    )
    visual = VisualEvidenceItem(
        keyframe_id="kf3",
        timestamp=32.0,
        frame_path="frames/kf3.jpg",
        raw_text="Formula: I = V * R",
        confidence=0.85,
        potential_equations=["I = V * R"],
    )

    state, conf, conflict, reason = policy.evaluate_fusion(speech, visual)
    assert state == FusionState.CONFLICT
    assert conflict is not None
    assert "conflict" in conflict.lower()


def test_case_4_visual_only_isolated(policy):
    """CASE 4: Visual displays formula, no relevant speech -> visual_only."""
    visual = VisualEvidenceItem(
        keyframe_id="kf4",
        timestamp=45.0,
        frame_path="frames/kf4.jpg",
        raw_text="I = V / R",
        confidence=0.89,
        potential_equations=["I = V / R"],
    )

    state, conf, conflict, reason = policy.evaluate_fusion(None, visual)
    assert state == FusionState.VISUAL_ONLY
    assert conf == 0.89
    assert conflict is None


def test_case_5_unrelated_domains_unsupported(policy):
    """CASE 5: Speech discusses Ohm's law, visual displays E = mc^2 -> unsupported."""
    speech = SpeechEvidenceItem(
        speech_id="s5",
        timestamp_start=50.0,
        timestamp_end=54.0,
        text="according to Ohm's law current is proportional to voltage",
        confidence=0.90,
    )
    visual = VisualEvidenceItem(
        keyframe_id="kf5",
        timestamp=52.0,
        frame_path="frames/kf5.jpg",
        raw_text="Einstein Theory: E = m * c^2",
        confidence=0.85,
        potential_equations=["E = m * c^2"],
    )

    state, conf, conflict, reason = policy.evaluate_fusion(speech, visual)
    assert state == FusionState.UNSUPPORTED
    assert conflict is None


def test_temporal_proximity_exceeded_unsupported(policy):
    """Speech and visual with large temporal delta (> 6s) are not fused as joint support."""
    speech = SpeechEvidenceItem(
        speech_id="s6",
        timestamp_start=10.0,
        timestamp_end=12.0,
        text="I = V / R",
        detected_math="I = V / R",
    )
    visual = VisualEvidenceItem(
        keyframe_id="kf6",
        timestamp=30.0,  # 19s delta > 6s window
        frame_path="frames/kf6.jpg",
        raw_text="I = V / R",
        confidence=0.9,
        potential_equations=["I = V / R"],
    )

    state, conf, conflict, reason = policy.evaluate_fusion(speech, visual)
    assert state == FusionState.UNSUPPORTED
    assert "exceeds window" in reason


def test_uncertain_ocr_confidence(policy):
    """Visual evidence with low confidence (< 0.45) yields uncertain state."""
    visual = VisualEvidenceItem(
        keyframe_id="kf_low",
        timestamp=10.0,
        frame_path="frames/low.jpg",
        raw_text="partial text",
        confidence=0.35,  # Below 0.45 threshold
    )
    state, conf, conflict, reason = policy.evaluate_fusion(None, visual)
    assert state == FusionState.UNCERTAIN
    assert conf == 0.35
