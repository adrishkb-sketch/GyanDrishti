"""Policy definitions and decision rules for multimodal evidence fusion.

Implements strict validation rules to prevent false multimodal agreement.
"""

from typing import Optional, Tuple
from .matcher import DeterministicMathMatcher
from .schemas import (
    FusionState,
    SpeechEvidenceItem,
    VisualEvidenceItem,
)


class FusionPolicy:
    """Evaluates multimodal evidence candidates against deterministic decision rules."""

    def __init__(
        self,
        proximity_window_seconds: float = 6.0,
        uncertainty_threshold: float = 0.45,
    ) -> None:
        self.proximity_window = proximity_window_seconds
        self.uncertainty_threshold = uncertainty_threshold

    def evaluate_fusion(
        self,
        speech: Optional[SpeechEvidenceItem],
        visual: Optional[VisualEvidenceItem],
    ) -> Tuple[FusionState, float, Optional[str], str]:
        """Classifies the relationship between speech and visual evidence.

        Returns:
            (FusionState, confidence_score, conflict_details, audit_reason)
        """
        # Case A: Isolated Speech
        if speech is not None and visual is None:
            return (
                FusionState.SPEECH_ONLY,
                speech.confidence or 0.85,
                None,
                "Speech segment occurred without proximate board activity.",
            )

        # Case B: Isolated Visual
        if visual is not None and speech is None:
            conf = visual.confidence
            state = FusionState.UNCERTAIN if conf < self.uncertainty_threshold else FusionState.VISUAL_ONLY
            return (
                state,
                conf,
                None,
                "Visual board evidence detected without corresponding spoken audio.",
            )

        if speech is None and visual is None:
            return (
                FusionState.UNSUPPORTED,
                0.0,
                None,
                "No evidence provided.",
            )

        # Case C: Both Speech and Visual Present
        # 1. Temporal Proximity Check
        s_mid = (speech.timestamp_start + speech.timestamp_end) / 2.0
        delta = abs(s_mid - visual.timestamp)

        if delta > self.proximity_window:
            # Beyond temporal association window -> Treated as independent events
            return (
                FusionState.UNSUPPORTED,
                0.3,
                None,
                f"Speech ({s_mid:.1f}s) and Visual ({visual.timestamp:.1f}s) temporal offset ({delta:.1f}s) exceeds window ({self.proximity_window:.1f}s).",
            )

        # 2. Check for Low Confidence Uncertainty
        if visual.confidence < self.uncertainty_threshold:
            return (
                FusionState.UNCERTAIN,
                visual.confidence,
                None,
                f"Visual OCR confidence ({visual.confidence:.2f}) below threshold ({self.uncertainty_threshold:.2f}).",
            )

        # 3. Extract Equations
        speech_eq = speech.detected_math or DeterministicMathMatcher.extract_math_from_speech(speech.text)
        visual_eq = visual.potential_equations[0] if visual.potential_equations else None

        # 4. Scenario: Both have equations
        if speech_eq and visual_eq:
            is_match, is_conflict, reason = DeterministicMathMatcher.compare_equations(speech_eq, visual_eq)

            if is_conflict:
                return (
                    FusionState.CONFLICT,
                    0.4,
                    reason,
                    f"Contradictory representations: Speech '{speech_eq}' vs Visual '{visual_eq}'.",
                )

            if is_match:
                # Joint multimodal support
                joint_conf = min(1.0, 0.5 + 0.5 * visual.confidence)
                return (
                    FusionState.MULTIMODAL_SUPPORTED,
                    round(joint_conf, 4),
                    None,
                    f"Multimodal consensus verified: Both speech and visual evidence confirm '{visual_eq}'.",
                )

            # Different equations present
            if DeterministicMathMatcher.conceptual_domain_match(speech.text, visual.raw_text):
                return (
                    FusionState.VISUAL_ONLY,
                    visual.confidence,
                    None,
                    f"Visual equation '{visual_eq}' not explicitly dictated in speech '{speech.text}'. Retained as visual-only.",
                )
            else:
                return (
                    FusionState.UNSUPPORTED,
                    0.2,
                    None,
                    f"Speech and visual equations belong to distinct domains: '{speech_eq}' vs '{visual_eq}'.",
                )

        # 5. Scenario: Visual has equation, Speech has qualitative conceptual explanation (CASE 2)
        if visual_eq and not speech_eq:
            # Check if speech is discussing the same topic conceptually
            if DeterministicMathMatcher.conceptual_domain_match(speech.text, visual.raw_text):
                return (
                    FusionState.VISUAL_ONLY,
                    visual.confidence,
                    None,
                    f"Visual equation '{visual_eq}' present on board during conceptual lecture discussion; equation was not spoken.",
                )
            else:
                # Completely unrelated (CASE 5)
                return (
                    FusionState.UNSUPPORTED,
                    0.2,
                    None,
                    f"Visual equation '{visual_eq}' unrelated to spoken phrase '{speech.text}'.",
                )

        # 6. Scenario: Speech has equation, Visual has no detected equation
        if speech_eq and not visual_eq:
            return (
                FusionState.SPEECH_ONLY,
                speech.confidence or 0.85,
                None,
                f"Equation '{speech_eq}' spoken by lecturer; not detected on visual board.",
            )

        # 7. Neither has equation - general multimodal text check
        if DeterministicMathMatcher.conceptual_domain_match(speech.text, visual.raw_text):
            return (
                FusionState.MULTIMODAL_SUPPORTED,
                round(0.5 + 0.5 * visual.confidence, 4),
                None,
                "Qualitative speech and visual board notes align in same conceptual domain.",
            )

        return (
            FusionState.UNSUPPORTED,
            0.2,
            None,
            "Speech and visual evidence co-occurred without semantic or mathematical consensus.",
        )
