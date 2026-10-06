"""Temporal association between spoken audio transcripts and visual OCR evidence.

Links timestamped speech segments with visual keyframes falling within temporal
proximity to establish multimodal evidence without modifying immutable sources.
"""

from typing import Any, Dict, List, Optional
from .schemas import MultimodalAssociation, VisualAnalysisResult


class TemporalVisualAssociator:
    """Associates visual text evidence with temporally proximate speech events."""

    def __init__(self, proximity_window_seconds: float = 7.5) -> None:
        self.proximity_window = proximity_window_seconds

    def associate(
        self,
        speech_events: List[Any],
        visual_results: List[VisualAnalysisResult],
        session_id: Optional[str] = None,
    ) -> List[MultimodalAssociation]:
        """Correlates speech events and visual keyframes based on temporal proximity.

        Args:
            speech_events: List of SpeechEvent instances or dicts with start, end, text
            visual_results: List of VisualAnalysisResult instances
            session_id: Optional session identifier
        """
        associations: List[MultimodalAssociation] = []
        assoc_idx = 1

        for s_idx, sp in enumerate(speech_events):
            if hasattr(sp, "start"):
                s_start = float(getattr(sp, "start"))
                s_end = float(getattr(sp, "end"))
                s_text = str(getattr(sp, "text", ""))
                s_id = getattr(sp, "id", None) or f"speech_seg_{s_idx+1:03d}"
            elif isinstance(sp, dict):
                s_start = float(sp.get("start", sp.get("start_time", 0.0)))
                s_end = float(sp.get("end", sp.get("end_time", 0.0)))
                s_text = str(sp.get("text", ""))
                s_id = sp.get("id") or f"speech_seg_{s_idx+1:03d}"
            else:
                continue

            s_mid = (s_start + s_end) / 2.0

            # Find visual keyframes within proximity window
            matched_visuals: List[VisualAnalysisResult] = []
            for vr in visual_results:
                if (s_start - self.proximity_window) <= vr.timestamp <= (s_end + self.proximity_window):
                    matched_visuals.append(vr)

            if not matched_visuals:
                # Speech-only evidence
                associations.append(
                    MultimodalAssociation(
                        id=f"assoc_{assoc_idx:04d}",
                        session_id=session_id,
                        speech_segment_id=s_id,
                        speech_text=s_text,
                        speech_timestamp_start=round(s_start, 2),
                        speech_timestamp_end=round(s_end, 2),
                        association_type="speech_only",
                        confidence=1.0,
                    )
                )
                assoc_idx += 1
            else:
                for vr in matched_visuals:
                    offset = round(abs(vr.timestamp - s_mid), 2)
                    joint_conf = round(0.5 + 0.5 * vr.overall_confidence, 4) if vr.extracted_text else 0.5

                    associations.append(
                        MultimodalAssociation(
                            id=f"assoc_{assoc_idx:04d}",
                            session_id=session_id,
                            speech_segment_id=s_id,
                            speech_text=s_text,
                            speech_timestamp_start=round(s_start, 2),
                            speech_timestamp_end=round(s_end, 2),
                            visual_keyframe_id=vr.keyframe_id,
                            visual_timestamp=round(vr.timestamp, 2),
                            visual_extracted_text=vr.raw_text_combined if vr.raw_text_combined else None,
                            temporal_offset_seconds=offset,
                            association_type="multimodal_grounded" if vr.extracted_text else "speech_only",
                            confidence=joint_conf,
                        )
                    )
                    assoc_idx += 1

        # Also register visual-only events that had no speech nearby
        speech_ranges = [
            (
                float(getattr(s, "start", s.get("start", 0.0) if isinstance(s, dict) else 0.0)),
                float(getattr(s, "end", s.get("end", 0.0) if isinstance(s, dict) else 0.0)),
            )
            for s in speech_events
        ]

        for vr in visual_results:
            is_associated = any(
                (start - self.proximity_window) <= vr.timestamp <= (end + self.proximity_window)
                for start, end in speech_ranges
            )
            if not is_associated and vr.extracted_text:
                associations.append(
                    MultimodalAssociation(
                        id=f"assoc_{assoc_idx:04d}",
                        session_id=session_id,
                        visual_keyframe_id=vr.keyframe_id,
                        visual_timestamp=round(vr.timestamp, 2),
                        visual_extracted_text=vr.raw_text_combined,
                        association_type="visual_only",
                        confidence=vr.overall_confidence,
                    )
                )
                assoc_idx += 1

        return associations
