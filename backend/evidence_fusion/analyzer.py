"""Analyzer pipeline adapter connecting temporal timeline and visual results to fusion."""

from typing import Any, List, Optional
from .fusion import MultimodalEvidenceFusor
from .matcher import DeterministicMathMatcher
from .schemas import (
    FusedEvidenceItem,
    MultimodalFusionReport,
    SpeechEvidenceItem,
    VisualEvidenceItem,
)


class FusionPipelineAnalyzer:
    """End-to-end pipeline analyzer linking raw upstream models to evidence fusion."""

    def __init__(self, fusor: Optional[MultimodalEvidenceFusor] = None) -> None:
        self.fusor = fusor or MultimodalEvidenceFusor()

    def process_pipeline(
        self,
        speech_events: List[Any],
        visual_results: List[Any],
        session_id: Optional[str] = None,
    ) -> MultimodalFusionReport:
        """Adapts raw speech events (from speech/temporal engine) and visual results (from visual intelligence)."""
        speech_items: List[SpeechEvidenceItem] = []
        for idx, s in enumerate(speech_events):
            if hasattr(s, "text"):
                t = getattr(s, "text")
                st = float(getattr(s, "start", 0.0))
                et = float(getattr(s, "end", st))
                c = getattr(s, "confidence", None)
                sid = getattr(s, "id", f"sp_{idx+1:03d}")
            elif isinstance(s, dict):
                t = s.get("text", "")
                st = float(s.get("start", s.get("start_time", 0.0)))
                et = float(s.get("end", s.get("end_time", st)))
                c = s.get("confidence")
                sid = s.get("id", f"sp_{idx+1:03d}")
            else:
                continue

            math_detected = DeterministicMathMatcher.extract_math_from_speech(t)
            speech_items.append(
                SpeechEvidenceItem(
                    speech_id=sid,
                    timestamp_start=st,
                    timestamp_end=et,
                    text=t,
                    confidence=c,
                    detected_math=math_detected,
                )
            )

        visual_items: List[VisualEvidenceItem] = []
        for v in visual_results:
            if hasattr(v, "keyframe_id"):
                kfid = getattr(v, "keyframe_id")
                ts = float(getattr(v, "timestamp", 0.0))
                fp = getattr(v, "source_image", "")
                txt = getattr(v, "raw_text_combined", "")
                conf = float(getattr(v, "overall_confidence", 0.0))
                eqs = list(getattr(v, "potential_equations", []))
            elif isinstance(v, dict):
                kfid = v.get("keyframe_id", "")
                ts = float(v.get("timestamp", 0.0))
                fp = v.get("source_image", v.get("frame_path", ""))
                txt = v.get("raw_text_combined", v.get("raw_text", ""))
                conf = float(v.get("overall_confidence", v.get("confidence", 0.0)))
                eqs = list(v.get("potential_equations", []))
            else:
                continue

            visual_items.append(
                VisualEvidenceItem(
                    keyframe_id=kfid,
                    timestamp=ts,
                    frame_path=fp,
                    raw_text=txt,
                    confidence=conf,
                    potential_equations=eqs,
                )
            )

        return self.fusor.fuse(
            speech_items=speech_items,
            visual_items=visual_items,
            session_id=session_id,
        )
