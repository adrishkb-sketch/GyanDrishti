"""Deterministic demonstration of Multimodal Evidence Fusion (Milestone 6).

Demonstrates the 5 core validation cases:
  Case 1: Spoken formula + Visual formula -> multimodal_supported
  Case 2: Qualitative speech + Visual formula -> visual_only (not claimed spoken)
  Case 3: Spoken I = V/R vs Visual I = V*R -> conflict
  Case 4: Visual formula without speech -> visual_only
  Case 5: Ohm's speech + E = mc^2 visual -> unsupported
"""

from evidence_fusion.fusion import MultimodalEvidenceFusor
from evidence_fusion.policies import FusionPolicy
from evidence_fusion.schemas import SpeechEvidenceItem, VisualEvidenceItem


def run_demo():
    print("=" * 80)
    print("GYANDRISHTI MULTIMODAL EVIDENCE FUSION DEMO (MILESTONE 6)")
    print("=" * 80)

    fusor = MultimodalEvidenceFusor(FusionPolicy(proximity_window_seconds=6.0))

    scenarios = [
        (
            "CASE 1: Speech states formula + Visual displays exact formula",
            SpeechEvidenceItem(
                speech_id="sp_case1",
                timestamp_start=10.0,
                timestamp_end=15.0,
                text="current is equal to voltage divided by resistance",
                confidence=0.94,
            ),
            VisualEvidenceItem(
                keyframe_id="kf_case1",
                timestamp=12.5,
                frame_path="frames/ohm_whiteboard.jpg",
                raw_text="Ohm's Law: I = V / R",
                confidence=0.91,
                potential_equations=["I = V / R"],
            ),
        ),
        (
            "CASE 2: Qualitative speech + Visual formula (DO NOT claim spoken)",
            SpeechEvidenceItem(
                speech_id="sp_case2",
                timestamp_start=25.0,
                timestamp_end=30.0,
                text="current increases when resistance decreases in this branch",
                confidence=0.90,
            ),
            VisualEvidenceItem(
                keyframe_id="kf_case2",
                timestamp=27.0,
                frame_path="frames/circuit_notes.jpg",
                raw_text="I = V / R",
                confidence=0.89,
                potential_equations=["I = V / R"],
            ),
        ),
        (
            "CASE 3: Contradictory formulations -> Conflict",
            SpeechEvidenceItem(
                speech_id="sp_case3",
                timestamp_start=40.0,
                timestamp_end=44.0,
                text="I = V / R",
                confidence=0.95,
                detected_math="I = V / R",
            ),
            VisualEvidenceItem(
                keyframe_id="kf_case3",
                timestamp=42.0,
                frame_path="frames/erroneous_board.jpg",
                raw_text="Formula: I = V * R",
                confidence=0.88,
                potential_equations=["I = V * R"],
            ),
        ),
        (
            "CASE 4: Visual formula without relevant speech",
            None,
            VisualEvidenceItem(
                keyframe_id="kf_case4",
                timestamp=60.0,
                frame_path="frames/silent_board.jpg",
                raw_text="Faraday's Law: V = - dPhi / dt",
                confidence=0.87,
                potential_equations=["V = - dPhi / dt"],
            ),
        ),
        (
            "CASE 5: Ohm's speech + E = mc^2 visual -> Unsupported / Unrelated",
            SpeechEvidenceItem(
                speech_id="sp_case5",
                timestamp_start=80.0,
                timestamp_end=85.0,
                text="according to Ohm's law voltage is proportional to current",
                confidence=0.92,
            ),
            VisualEvidenceItem(
                keyframe_id="kf_case5",
                timestamp=82.0,
                frame_path="frames/einstein_slide.jpg",
                raw_text="Relativity: E = m * c^2",
                confidence=0.93,
                potential_equations=["E = m * c^2"],
            ),
        ),
    ]

    for title, sp, vr in scenarios:
        print("\n" + "-" * 80)
        print(title)
        print("-" * 80)
        if sp:
            print(f"Speech ({sp.timestamp_start}s–{sp.timestamp_end}s): \"{sp.text}\"")
        else:
            print("Speech: None")

        if vr:
            print(f"Visual ({vr.timestamp}s): OCR=\"{vr.raw_text}\" | Equations={vr.potential_equations}")
        else:
            print("Visual: None")

        speech_list = [sp] if sp else []
        visual_list = [vr] if vr else []
        report = fusor.fuse(speech_list, visual_list, session_id="demo_session")
        fused = report.fused_items[0]

        print(f"\n→ FUSED STATE:            {fused.state.value.upper()}")
        print(f"→ FUSION CONFIDENCE:      {fused.fusion_confidence:.2f}")
        if fused.canonical_representation:
            print(f"→ CANONICAL FORMULA:      {fused.canonical_representation}")
        if fused.conflict_details:
            print(f"→ CONFLICT DETAILS:       {fused.conflict_details}")
        print(f"→ AUDIT REASON:           {fused.notes}")

    print("\n" + "=" * 80)
    print("DEMO COMPLETE — 100% Deterministic, Offline, Zero LLM Hallucinations.")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
