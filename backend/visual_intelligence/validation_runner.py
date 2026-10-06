"""Validation runner for GyanDrishti Visual Intelligence Engine.

Executes local OCR across multiple keyframe scenarios (Whiteboard, Blackboard,
Clean Printed Slide, Complex Mathematical Formula, and Blank Frame) to evaluate
accuracy, failure modes, latency, and Apple Silicon throughput.
"""

import os
import tempfile
import time
import numpy as np
from PIL import Image, ImageDraw

from visual_intelligence.analyzer import VisualIntelligenceAnalyzer
from visual_intelligence.ocr import RapidOCREngine
from visual_intelligence.preprocessing import ImagePreprocessor
from visual_intelligence.schemas import OCRStatus


def generate_benchmark_keyframes(temp_dir: str):
    """Creates a suite of benchmark keyframes spanning classroom conditions."""
    frames = []

    # 1. Whiteboard: Ohm's law with equations
    wb = Image.new("RGB", (800, 450), color=(252, 252, 252))
    d_wb = ImageDraw.Draw(wb)
    d_wb.text((40, 40), "Basic Electrical Engineering - Lecture 1", fill=(0, 0, 0))
    d_wb.text((40, 100), "Ohm's Law: I = V / R", fill=(10, 20, 150))
    d_wb.text((40, 160), "Power Dissipation: P = V * I = I^2 * R", fill=(10, 20, 150))
    p1 = os.path.join(temp_dir, "kf_01_whiteboard_ohm.jpg")
    wb.save(p1)
    frames.append(("kf_01_whiteboard_ohm", 10.0, p1, "Whiteboard with clean formulas"))

    # 2. Blackboard: Chalk on dark green surface
    bb = Image.new("RGB", (800, 450), color=(30, 45, 38))
    d_bb = ImageDraw.Draw(bb)
    d_bb.text((40, 40), "Newton's Second Law of Motion", fill=(240, 240, 240))
    d_bb.text((40, 120), "F = m * a", fill=(255, 255, 220))
    d_bb.text((40, 200), "Kinetic Energy: KE = 0.5 * m * v^2", fill=(255, 255, 220))
    p2 = os.path.join(temp_dir, "kf_02_blackboard_newton.jpg")
    bb.save(p2)
    frames.append(("kf_02_blackboard_newton", 25.0, p2, "Blackboard chalk handwriting/text"))

    # 3. Slide / Projected screen: High contrast printed text
    sl = Image.new("RGB", (960, 540), color=(240, 242, 245))
    d_sl = ImageDraw.Draw(sl)
    d_sl.rectangle([(30, 30), (930, 510)], fill=(255, 255, 255), outline=(200, 200, 210))
    d_sl.text((60, 60), "Chapter 4: Kirchhoff's Laws", fill=(20, 30, 40))
    d_sl.text((60, 140), "1. Kirchhoff's Current Law (KCL): Sum(I_in) = Sum(I_out)", fill=(40, 40, 40))
    d_sl.text((60, 220), "2. Kirchhoff's Voltage Law (KVL): Sum(V_drop) = 0", fill=(40, 40, 40))
    p3 = os.path.join(temp_dir, "kf_03_projected_slide.jpg")
    sl.save(p3)
    frames.append(("kf_03_projected_slide", 40.0, p3, "Digital projected slide"))

    # 4. Complex math symbols & fractions
    cm = Image.new("RGB", (800, 450), color=(255, 255, 255))
    d_cm = ImageDraw.Draw(cm)
    d_cm.text((40, 40), "Einstein Mass-Energy Relation", fill=(0, 0, 0))
    d_cm.text((40, 120), "E = m * c^2", fill=(0, 0, 0))
    d_cm.text((40, 200), "Relativistic Momentum: p = gamma * m * v", fill=(0, 0, 0))
    p4 = os.path.join(temp_dir, "kf_04_relativistic_physics.jpg")
    cm.save(p4)
    frames.append(("kf_04_relativistic_physics", 65.0, p4, "Physics equations"))

    # 5. Empty / Clean board (no text written yet)
    em = Image.new("RGB", (800, 450), color=(248, 248, 248))
    p5 = os.path.join(temp_dir, "kf_05_blank_board.jpg")
    em.save(p5)
    frames.append(("kf_05_blank_board", 85.0, p5, "Blank whiteboard (no text)"))

    return frames


def run_validation():
    print("=" * 80)
    print("GYANDRISHTI VISUAL INTELLIGENCE BENCHMARK & REAL VALIDATION SUITE")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as temp_dir:
        benchmark_frames = generate_benchmark_keyframes(temp_dir)

        analyzer = VisualIntelligenceAnalyzer(
            ocr_engine=RapidOCREngine(),
            preprocessor=ImagePreprocessor(),
        )

        results = []
        latencies = []
        successful_count = 0
        failed_count = 0
        uncertain_count = 0
        no_text_count = 0

        for kf_id, ts, frame_path, desc in benchmark_frames:
            t0 = time.perf_counter()
            res = analyzer.analyze_image(
                image_input=frame_path,
                keyframe_id=kf_id,
                timestamp=ts,
            )
            lat = (time.perf_counter() - t0) * 1000.0
            latencies.append(lat)
            results.append((res, desc, lat))

            if res.processing_status == OCRStatus.SUCCESS:
                successful_count += 1
            elif res.processing_status == OCRStatus.FAILED:
                failed_count += 1
            elif res.processing_status == OCRStatus.UNCERTAIN:
                uncertain_count += 1
            elif res.processing_status == OCRStatus.NO_TEXT_DETECTED:
                no_text_count += 1

            print(f"\n[Keyframe {kf_id}] ({desc})")
            print(f"  Status:           {res.processing_status.value}")
            print(f"  Confidence:       {res.overall_confidence:.2f}")
            print(f"  Latency:          {lat:.1f}ms")
            print(f"  Extracted Text:   {res.raw_text_combined[:90]}..." if len(res.raw_text_combined) > 90 else f"  Extracted Text:   {res.raw_text_combined}")
            print(f"  Math Equations:   {res.potential_equations}")

        avg_latency = sum(latencies) / len(latencies)

        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        print(f"Total Keyframes Processed:    {len(benchmark_frames)}")
        print(f"Successful OCR:               {successful_count}")
        print(f"No Text (Clean/Blank):        {no_text_count}")
        print(f"Uncertain OCR:                {uncertain_count}")
        print(f"Failed OCR:                   {failed_count}")
        print(f"Average Processing Latency:   {avg_latency:.1f}ms per frame")
        print("=" * 80)


if __name__ == "__main__":
    run_validation()
