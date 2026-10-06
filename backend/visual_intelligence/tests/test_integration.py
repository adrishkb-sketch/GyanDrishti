"""Integration tests between Visual Intelligence and Lecture Memory Engine."""

import pytest
from lecture_memory.builder import LectureMemoryBuilder
from lecture_memory.schemas import LectureMemory
from temporal_engine.schemas import LectureTimeline, TimelineEvent, VisualEvent
from understanding_engine.schemas import LectureUnderstanding, VisualReference
from visual_intelligence.schemas import OCRStatus, VisualAnalysisResult, VisualTextEvidence


def test_18_lecture_memory_serialization_valid_with_ocr_evidence():
    """Requirement 18: Lecture Memory serialization remains valid after adding OCR evidence."""
    # 1. Create a sample understanding with visual reference candidate
    understanding = LectureUnderstanding(
        time_start=0.0,
        time_end=30.0,
        topic="Physics",
        visual_references=[
            VisualReference(
                timestamp=14.5,
                source="camera",
                event_type="board_change",
                frame_path="recordings/frames/camera_f014_14500.jpg",
                relevance="Board contains circuit formula",
            )
        ],
    )

    # 2. Create OCR analysis result
    ocr_item = VisualTextEvidence(
        id="camera_f014_14500_ocr_001",
        keyframe_id="camera_f014_14500",
        timestamp=14.5,
        text="I = V / R",
        confidence=0.94,
        source_image="recordings/frames/camera_f014_14500.jpg",
        is_potential_math=True,
    )
    analysis_result = VisualAnalysisResult(
        keyframe_id="camera_f014_14500",
        timestamp=14.5,
        source_image="recordings/frames/camera_f014_14500.jpg",
        extracted_text=[ocr_item],
        raw_text_combined="I = V / R",
        overall_confidence=0.94,
        processing_status=OCRStatus.SUCCESS,
        potential_equations=["I = V / R"],
    )

    # 3. Build Lecture Memory with visual analysis
    memory = LectureMemoryBuilder.build(
        understandings=[understanding],
        session_id="lecture_vi_test_01",
        visual_analysis=[analysis_result],
    )

    # 4. Verify enriched visual reference
    assert len(memory.visual_references) >= 1
    vr = memory.visual_references[0]
    assert vr.extracted_text == "I = V / R"
    assert vr.ocr_confidence == 0.94
    assert vr.ocr_status == "success"
    assert vr.potential_equations == ["I = V / R"]

    # 5. Verify lossless JSON serialization round-trip
    json_str = memory.to_json()
    reloaded = LectureMemory.from_json(json_str)

    assert reloaded.session_id == memory.session_id
    assert len(reloaded.visual_references) == len(memory.visual_references)
    assert reloaded.visual_references[0].extracted_text == "I = V / R"
    assert reloaded.visual_references[0].ocr_confidence == 0.94
    assert reloaded.visual_references[0].ocr_status == "success"

    # 6. Verify frontend dictionary export
    fe_dict = memory.to_frontend_dict()
    assert "visual_references" in fe_dict
    fe_vr = fe_dict["visual_references"][0]
    assert fe_vr["extracted_text"] == "I = V / R"
    assert fe_vr["ocr_confidence"] == 0.94
    assert fe_vr["ocr_status"] == "success"
    assert fe_vr["local_frame_reference"] == "recordings/frames/camera_f014_14500.jpg"
