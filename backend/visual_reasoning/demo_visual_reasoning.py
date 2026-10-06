"""Demonstration of Local Visual Reasoning and Diagram Understanding (Milestone 7).

Demonstrates:
  Keyframe Image
       ↓
  OCR Ground Truth ("I = V / R")
       +
  Local VLM Proposal (Circuit Diagram, Battery, Resistor)
       ↓
  Deterministic Validation (Agreement vs Conflict)
       ↓
  Audited Visual Reasoning Record
"""

from visual_reasoning.analyzer import VisualReasoningAnalyzer
from visual_reasoning.provider import MockVLMProvider
from visual_reasoning.schemas import (
    DiagramType,
    VisualReasoningProposal,
)


def run_demo():
    print("=" * 80)
    print("GYANDRISHTI LOCAL VISUAL REASONING & DIAGRAM UNDERSTANDING DEMO (M7)")
    print("=" * 80)

    # 1. Scenario A: Agreement between Diagram VLM and Board OCR
    print("\n--- SCENARIO A: Diagram Understanding with OCR Agreement ---")
    proposal_a = VisualReasoningProposal(
        model_name="qwen2-vl:2b (local open-weight)",
        model_version="q4_k_m",
        diagram_type=DiagramType.CIRCUIT_DIAGRAM,
        description="Schematic showing DC voltage source connected in series with resistor R1.",
        entities_detected=["DC Voltage Source (V)", "Resistor (R1)", "Conducting Loop"],
        relations_detected=["V connects to R1 across node A-B"],
        visible_equations=["I = V / R"],
        confidence=0.91,
    )

    analyzer_a = VisualReasoningAnalyzer(provider=MockVLMProvider(default_proposal=proposal_a))
    res_a = analyzer_a.analyze_keyframe(
        image_path="recordings/circuit_diagram.jpg",
        keyframe_id="camera_f015_15000",
        timestamp=15.0,
        raw_ocr_text="Verified Board OCR: I = V / R",
        ocr_equations=["I = V / R"],
    )

    print(f"Keyframe:                 {res_a.keyframe_id} ({res_a.timestamp:.1f}s)")
    print(f"Diagram Type:             {res_a.proposal.diagram_type.value}")
    print(f"Description:              {res_a.proposal.description}")
    print(f"Entities Detected:        {res_a.proposal.entities_detected}")
    print(f"Raw OCR Evidence:         \"{res_a.raw_ocr_text}\" (Immutable)")
    print(f"Validation Status:        {res_a.validation_status.value.upper()}")
    print(f"Notes:                    {res_a.conflict_notes}")

    # 2. Scenario B: Mathematical Contradiction between VLM and OCR
    print("\n--- SCENARIO B: Contradiction Detected (Raw OCR Protected) ---")
    proposal_b = VisualReasoningProposal(
        model_name="qwen2-vl:2b (local open-weight)",
        diagram_type=DiagramType.CIRCUIT_DIAGRAM,
        description="Erroneous VLM claiming product relationship.",
        entities_detected=["Battery", "Resistor"],
        visible_equations=["I = V * R"],  # Contradicts OCR!
        confidence=0.75,
    )

    analyzer_b = VisualReasoningAnalyzer(provider=MockVLMProvider(default_proposal=proposal_b))
    res_b = analyzer_b.analyze_keyframe(
        image_path="recordings/circuit_diagram.jpg",
        keyframe_id="camera_f015_15000",
        timestamp=15.0,
        raw_ocr_text="Board OCR: I = V / R",
        ocr_equations=["I = V / R"],
    )

    print(f"Keyframe:                 {res_b.keyframe_id}")
    print(f"VLM Claim:                {res_b.proposal.visible_equations}")
    print(f"OCR Ground Truth:         \"{res_b.raw_ocr_text}\"")
    print(f"Validation Status:        {res_b.validation_status.value.upper()}")
    print(f"Conflict Audit:           {res_b.conflict_notes}")

    print("\n" + "=" * 80)
    print("DEMO COMPLETE — Local, Open-Weight Compatible, Zero OCR Mutation.")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
