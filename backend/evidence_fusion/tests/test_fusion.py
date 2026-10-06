"""Tests for MultimodalEvidenceFusor and FusionPipelineAnalyzer."""

import pytest
from evidence_fusion.analyzer import FusionPipelineAnalyzer
from evidence_fusion.fusion import MultimodalEvidenceFusor
from evidence_fusion.schemas import (
    FusionState,
    SpeechEvidenceItem,
    VisualEvidenceItem,
)


def test_fusor_end_to_end_report():
    fusor = MultimodalEvidenceFusor()

    speech_items = [
        SpeechEvidenceItem(
            speech_id="sp_01",
            timestamp_start=10.0,
            timestamp_end=15.0,
            text="current is equal to voltage divided by resistance",
            confidence=0.92,
        ),
        SpeechEvidenceItem(
            speech_id="sp_02",
            timestamp_start=40.0,
            timestamp_end=45.0,
            text="and next we consider the magnetic field",
            confidence=0.88,
        ),
    ]

    visual_items = [
        VisualEvidenceItem(
            keyframe_id="kf_01",
            timestamp=12.5,
            frame_path="frames/kf_01.jpg",
            raw_text="I = V / R",
            confidence=0.91,
            potential_equations=["I = V / R"],
        ),
        VisualEvidenceItem(
            keyframe_id="kf_02",
            timestamp=70.0,
            frame_path="frames/kf_02.jpg",
            raw_text="Board Diagram",
            confidence=0.85,
        ),
    ]

    report = fusor.fuse(speech_items, visual_items, session_id="sess_fuse_01")

    assert report.session_id == "sess_fuse_01"
    assert report.total_speech_segments == 2
    assert report.total_visual_keyframes == 2

    assert report.multimodal_supported_count >= 1
    assert report.speech_only_count >= 1
    assert report.visual_only_count >= 1


def test_fusion_preserves_audit_identifiers():
    fusor = MultimodalEvidenceFusor()
    speech = [
        SpeechEvidenceItem(
            speech_id="sp_exact_007",
            timestamp_start=12.0,
            timestamp_end=16.0,
            text="I equals V divided by R",
            confidence=0.94,
        )
    ]
    visual = [
        VisualEvidenceItem(
            keyframe_id="camera_f042_14000",
            timestamp=14.0,
            frame_path="recordings/camera_f042.jpg",
            raw_text="I = V / R",
            confidence=0.95,
            potential_equations=["I = V / R"],
        )
    ]

    report = fusor.fuse(speech, visual, session_id="test_sess")
    assert len(report.fused_items) == 1
    fused = report.fused_items[0]

    assert fused.state == FusionState.MULTIMODAL_SUPPORTED
    assert fused.speech_evidence.speech_id == "sp_exact_007"
    assert fused.visual_evidence.keyframe_id == "camera_f042_14000"
    assert fused.temporal_delta == 0.0  # (12 + 16)/2 = 14.0, delta |14.0 - 14.0| = 0.0
    assert fused.canonical_representation == "I = V / R"


def test_pipeline_analyzer_with_dicts():
    analyzer = FusionPipelineAnalyzer()

    raw_speech = [
        {
            "id": "dict_sp_1",
            "start": 5.0,
            "end": 9.0,
            "text": "voltage is current times resistance",
            "confidence": 0.90,
        }
    ]
    raw_visual = [
        {
            "keyframe_id": "dict_kf_1",
            "timestamp": 7.0,
            "frame_path": "frames/f.jpg",
            "raw_text_combined": "V = I * R",
            "overall_confidence": 0.88,
            "potential_equations": ["V = I * R"],
        }
    ]

    report = analyzer.process_pipeline(raw_speech, raw_visual, session_id="sess_pipe")
    assert report.session_id == "sess_pipe"
    assert report.multimodal_supported_count == 1
    item = report.fused_items[0]
    assert item.state == FusionState.MULTIMODAL_SUPPORTED
    assert item.canonical_representation == "V = I * R"


def test_deterministic_repeatability():
    """Identical inputs produce identical fused output byte-for-byte."""
    fusor = MultimodalEvidenceFusor()
    speech = [
        SpeechEvidenceItem(
            speech_id="s1",
            timestamp_start=1.0,
            timestamp_end=3.0,
            text="F equals m times a",
        )
    ]
    visual = [
        VisualEvidenceItem(
            keyframe_id="v1",
            timestamp=2.0,
            frame_path="f.jpg",
            raw_text="F = m * a",
            confidence=0.9,
            potential_equations=["F = m * a"],
        )
    ]

    r1 = fusor.fuse(speech, visual, session_id="rep_sess")
    r2 = fusor.fuse(speech, visual, session_id="rep_sess")

    assert r1.model_dump_json() == r2.model_dump_json()


def test_zero_llm_invoked():
    fusor = MultimodalEvidenceFusor()
    assert not hasattr(fusor, "llm")
    assert not hasattr(fusor, "client")
    assert not hasattr(fusor, "generate")
