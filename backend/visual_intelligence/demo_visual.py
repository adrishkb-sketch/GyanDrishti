"""Offline, local demonstration of GyanDrishti Visual Intelligence Engine.

Demonstrates:
  Keyframe Image
        ↓
  Preprocessing (Grayscale, CLAHE, Blackboard Inversion)
        ↓
  Local OCR (RapidOCR onnxruntime)
        ↓
  VisualTextEvidence & Mathematical Filtering
        ↓
  Temporal Multimodal Association
        ↓
  Enriched Lecture Memory Visual Reference
"""

import os
import tempfile
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from lecture_memory.builder import LectureMemoryBuilder
from temporal_engine.schemas import LectureTimeline, TimelineEvent, VisualEvent
from understanding_engine.schemas import LectureUnderstanding, VisualReference
from visual_intelligence.analyzer import VisualIntelligenceAnalyzer
from visual_intelligence.association import TemporalVisualAssociator
from visual_intelligence.ocr import RapidOCREngine
from visual_intelligence.preprocessing import ImagePreprocessor


def create_demo_frames(temp_dir: str):
    """Generates synthetic classroom whiteboard and blackboard frames."""
    # 1. Whiteboard frame: Ohm's law with formula
    wb_img = Image.new("RGB", (640, 360), color=(250, 250, 250))
    draw_wb = ImageDraw.Draw(wb_img)
    draw_wb.rectangle([(20, 20), (620, 340)], outline=(180, 180, 180), width=2)
    draw_wb.text((50, 50), "Ohm's Law Formulation", fill=(20, 20, 20))
    draw_wb.text((50, 110), "I = V / R", fill=(10, 10, 180))
    draw_wb.text((50, 180), "Where: I is Current, V is Voltage, R is Resistance", fill=(50, 50, 50))
    draw_wb.text((50, 240), "V = I * R", fill=(10, 10, 180))

    wb_path = os.path.join(temp_dir, "whiteboard_ohms_law.jpg")
    wb_img.save(wb_path, quality=95)

    # 2. Blackboard frame: Dark background with chalk text
    bb_img = Image.new("RGB", (640, 360), color=(35, 42, 38))
    draw_bb = ImageDraw.Draw(bb_img)
    draw_bb.rectangle([(20, 20), (620, 340)], outline=(60, 70, 65), width=2)
    draw_bb.text((50, 60), "Circuit Analysis - Node 1", fill=(235, 235, 235))
    draw_bb.text((50, 130), "KCL: Sum of currents = 0", fill=(245, 245, 220))
    draw_bb.text((50, 200), "I1 + I2 + I3 = 0", fill=(245, 245, 220))

    bb_path = os.path.join(temp_dir, "blackboard_kcl.jpg")
    bb_img.save(bb_path, quality=95)

    return wb_path, bb_path


def run_demo():
    print("=" * 80)
    print("GYANDRISHTI VISUAL INTELLIGENCE & BOARD UNDERSTANDING DEMO")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as temp_dir:
        wb_path, bb_path = create_demo_frames(temp_dir)

        analyzer = VisualIntelligenceAnalyzer(
            ocr_engine=RapidOCREngine(),
            preprocessor=ImagePreprocessor(),
        )

        test_frames = [
            ("camera_f012_15000", 15.0, wb_path, "Whiteboard"),
            ("camera_f034_32000", 32.0, bb_path, "Blackboard"),
        ]

        analysis_results = []

        print("\n[PHASE 1] Analyzing Keyframes via Local Offline OCR...")
        for kf_id, ts, frame_path, board_type in test_frames:
            print("-" * 80)
            result = analyzer.analyze_image(
                image_input=frame_path,
                keyframe_id=kf_id,
                timestamp=ts,
                session_id="lecture_demo_visual_01",
            )
            analysis_results.append(result)

            print(f"Keyframe:                 {result.keyframe_id} ({board_type})")
            print(f"Timestamp:                {result.timestamp:.1f}s")
            print(f"OCR Status:               {result.processing_status.value}")
            print(f"Extracted Text:           {result.raw_text_combined}")
            print(f"Confidence:               {result.overall_confidence:.2f}")
            print(f"Potential Equations:      {result.potential_equations}")
            print(f"Latency:                  {result.latency_ms:.1f}ms")

        print("\n" + "=" * 80)
        print("[PHASE 2] Temporal Multimodal Association with Spoken Timeline...")
        print("=" * 80)

        spoken_segments = [
            {
                "id": "speech_001",
                "start": 12.0,
                "end": 18.0,
                "text": "current is equal to voltage divided by resistance according to Ohm's law",
            },
            {
                "id": "speech_002",
                "start": 30.0,
                "end": 35.0,
                "text": "at the circuit node the sum of currents equals zero by Kirchhoff's current law",
            },
        ]

        associator = TemporalVisualAssociator(proximity_window_seconds=6.0)
        associations = associator.associate(
            speech_events=spoken_segments,
            visual_results=analysis_results,
            session_id="lecture_demo_visual_01",
        )

        for assoc in associations:
            print(f"\nAssociation ID:       {assoc.id}")
            print(f"Type:                 {assoc.association_type}")
            print(f"Speech ID:            {assoc.speech_segment_id} ({assoc.speech_timestamp_start}s–{assoc.speech_timestamp_end}s)")
            print(f"Spoken Text:          \"{assoc.speech_text}\"")
            print(f"Visual Keyframe:      {assoc.visual_keyframe_id} ({assoc.visual_timestamp}s)")
            print(f"Board OCR:            \"{assoc.visual_extracted_text}\"")
            print(f"Temporal Delta:       {assoc.temporal_offset_seconds}s")
            print(f"Joint Confidence:     {assoc.confidence:.2f}")

        print("\n" + "=" * 80)
        print("[PHASE 3] Ingesting Visual Evidence into Lecture Memory...")
        print("=" * 80)

        understanding = LectureUnderstanding(
            time_start=0.0,
            time_end=45.0,
            topic="Basic Electrical Engineering",
            visual_references=[
                VisualReference(
                    timestamp=15.0,
                    source="camera",
                    event_type="board_writing",
                    frame_path=wb_path,
                    relevance="Instructor wrote Ohm's law formula on whiteboard",
                ),
                VisualReference(
                    timestamp=32.0,
                    source="camera",
                    event_type="board_writing",
                    frame_path=bb_path,
                    relevance="Instructor wrote KCL equation on blackboard",
                ),
            ],
        )

        lecture_memory = LectureMemoryBuilder.build(
            understandings=[understanding],
            session_id="lecture_demo_visual_01",
            title="Introduction to Electrical Circuits",
            subject="Electrical Engineering",
            visual_analysis=analysis_results,
        )

        print(f"\nLecture Memory Session:   {lecture_memory.session_id}")
        print(f"Visual References Enriched: {len(lecture_memory.visual_references)}")

        for idx, vr in enumerate(lecture_memory.visual_references):
            print(f"\n--- Visual Reference #{idx+1} ---")
            print(f"Timestamp:              {vr.timestamp:.1f}s")
            print(f"Event Type:             {vr.event_type}")
            print(f"Local Frame:            {vr.local_frame_reference}")
            print(f"OCR Status:             {vr.ocr_status}")
            print(f"Extracted Text:         {vr.extracted_text}")
            print(f"OCR Confidence:         {vr.ocr_confidence}")
            print(f"Potential Equations:    {vr.potential_equations}")
            print(f"Provenance Source:      {vr.provenance.source_type}")

        print("\n[SUCCESS] Visual intelligence pipeline executed 100% locally with zero cloud dependencies.")


if __name__ == "__main__":
    run_demo()
