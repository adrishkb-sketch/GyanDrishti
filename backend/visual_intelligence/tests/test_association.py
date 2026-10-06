"""Tests for temporal association between speech and visual OCR evidence."""

import pytest
from visual_intelligence.association import TemporalVisualAssociator
from visual_intelligence.schemas import OCRStatus, VisualAnalysisResult, VisualTextEvidence


def test_16_speech_and_visual_evidence_linked_via_temporal_ids():
    """Requirement 16: Speech + visual evidence can be linked using existing temporal IDs."""
    associator = TemporalVisualAssociator(proximity_window_seconds=5.0)

    # Spoken segment at 12.0s - 18.0s
    speech_events = [
        {
            "id": "speech_seg_012",
            "start": 12.0,
            "end": 18.0,
            "text": "current is equal to voltage divided by resistance",
        }
    ]

    # Visual keyframe captured at 15.0s with OCR
    ocr_ev = VisualTextEvidence(
        id="kf_01_ocr_1",
        keyframe_id="camera_f012_15000",
        timestamp=15.0,
        text="I = V / R",
        confidence=0.92,
        source_image="frames/f012.jpg",
        is_potential_math=True,
    )
    visual_results = [
        VisualAnalysisResult(
            keyframe_id="camera_f012_15000",
            timestamp=15.0,
            source_image="frames/f012.jpg",
            extracted_text=[ocr_ev],
            raw_text_combined="I = V / R",
            overall_confidence=0.92,
            processing_status=OCRStatus.SUCCESS,
            potential_equations=["I = V / R"],
        )
    ]

    associations = associator.associate(
        speech_events=speech_events,
        visual_results=visual_results,
        session_id="lecture_session_01",
    )

    assert len(associations) == 1
    assoc = associations[0]
    assert assoc.speech_segment_id == "speech_seg_012"
    assert assoc.visual_keyframe_id == "camera_f012_15000"
    assert assoc.association_type == "multimodal_grounded"
    assert assoc.visual_extracted_text == "I = V / R"
    assert assoc.temporal_offset_seconds == 0.0  # (12 + 18)/2 = 15.0, offset |15.0 - 15.0| = 0.0
    assert assoc.confidence > 0.9


def test_speech_only_and_visual_only_associations():
    """Distinguishes isolated speech and isolated board writing events outside window."""
    associator = TemporalVisualAssociator(proximity_window_seconds=3.0)

    # Speech at 0s-5s
    speech = [{"id": "sp_1", "start": 0.0, "end": 5.0, "text": "Hello students"}]
    # Visual at 25s (far apart)
    visuals = [
        VisualAnalysisResult(
            keyframe_id="kf_far",
            timestamp=25.0,
            source_image="frames/far.jpg",
            extracted_text=[
                VisualTextEvidence(
                    id="ev_far",
                    keyframe_id="kf_far",
                    timestamp=25.0,
                    text="Formula Reference",
                    confidence=0.8,
                    source_image="frames/far.jpg",
                )
            ],
            raw_text_combined="Formula Reference",
            overall_confidence=0.8,
        )
    ]

    associations = associator.associate(speech, visuals)
    types = [a.association_type for a in associations]
    assert "speech_only" in types
    assert "visual_only" in types
    assert "multimodal_grounded" not in types
