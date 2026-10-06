"""Fusor engine for synthesizing speech and visual streams into audited fused items."""

from typing import Any, List, Optional
from .policies import FusionPolicy
from .schemas import (
    FusedEvidenceItem,
    FusionState,
    MultimodalFusionReport,
    SpeechEvidenceItem,
    VisualEvidenceItem,
)


class MultimodalEvidenceFusor:
    """Consolidates speech segments and visual analysis results into audited fused evidence."""

    def __init__(self, policy: Optional[FusionPolicy] = None) -> None:
        self.policy = policy or FusionPolicy()

    def fuse(
        self,
        speech_items: List[SpeechEvidenceItem],
        visual_items: List[VisualEvidenceItem],
        session_id: Optional[str] = None,
    ) -> MultimodalFusionReport:
        """Executes deterministic evidence fusion across speech and visual streams."""
        fused_items: List[FusedEvidenceItem] = []
        item_id = 1

        matched_visual_keys = set()

        for sp in speech_items:
            s_mid = (sp.timestamp_start + sp.timestamp_end) / 2.0
            # Find candidate visual items within proximity
            candidates = [
                v for v in visual_items
                if abs(v.timestamp - s_mid) <= self.policy.proximity_window
            ]

            if not candidates:
                state, conf, conflict, reason = self.policy.evaluate_fusion(sp, None)
                fused_items.append(
                    FusedEvidenceItem(
                        id=f"fused_{item_id:04d}",
                        session_id=session_id,
                        state=state,
                        primary_concept=sp.detected_math or sp.text[:60],
                        canonical_representation=sp.detected_math,
                        speech_evidence=sp,
                        visual_evidence=None,
                        temporal_delta=None,
                        fusion_confidence=conf,
                        conflict_details=conflict,
                        notes=reason,
                    )
                )
                item_id += 1
            else:
                for vr in candidates:
                    matched_visual_keys.add(vr.keyframe_id)
                    delta = round(abs(vr.timestamp - s_mid), 2)
                    state, conf, conflict, reason = self.policy.evaluate_fusion(sp, vr)

                    concept = (
                        vr.potential_equations[0]
                        if vr.potential_equations
                        else (sp.detected_math or sp.text[:60])
                    )

                    fused_items.append(
                        FusedEvidenceItem(
                            id=f"fused_{item_id:04d}",
                            session_id=session_id,
                            state=state,
                            primary_concept=concept,
                            canonical_representation=vr.potential_equations[0] if vr.potential_equations else sp.detected_math,
                            speech_evidence=sp,
                            visual_evidence=vr,
                            temporal_delta=delta,
                            fusion_confidence=conf,
                            conflict_details=conflict,
                            notes=reason,
                        )
                    )
                    item_id += 1

        # Check for isolated visual items that had no proximate speech
        for vr in visual_items:
            if vr.keyframe_id not in matched_visual_keys:
                state, conf, conflict, reason = self.policy.evaluate_fusion(None, vr)
                concept = vr.potential_equations[0] if vr.potential_equations else vr.raw_text[:60]
                fused_items.append(
                    FusedEvidenceItem(
                        id=f"fused_{item_id:04d}",
                        session_id=session_id,
                        state=state,
                        primary_concept=concept,
                        canonical_representation=vr.potential_equations[0] if vr.potential_equations else None,
                        speech_evidence=None,
                        visual_evidence=vr,
                        temporal_delta=None,
                        fusion_confidence=conf,
                        conflict_details=conflict,
                        notes=reason,
                    )
                )
                item_id += 1

        # Summary statistics
        mm_count = sum(1 for f in fused_items if f.state == FusionState.MULTIMODAL_SUPPORTED)
        vis_count = sum(1 for f in fused_items if f.state == FusionState.VISUAL_ONLY)
        sp_count = sum(1 for f in fused_items if f.state == FusionState.SPEECH_ONLY)
        conf_count = sum(1 for f in fused_items if f.state == FusionState.CONFLICT)
        unc_count = sum(1 for f in fused_items if f.state == FusionState.UNCERTAIN)
        unsupp_count = sum(1 for f in fused_items if f.state == FusionState.UNSUPPORTED)

        return MultimodalFusionReport(
            session_id=session_id or "default_session",
            total_speech_segments=len(speech_items),
            total_visual_keyframes=len(visual_items),
            fused_items=fused_items,
            multimodal_supported_count=mm_count,
            visual_only_count=vis_count,
            speech_only_count=sp_count,
            conflict_count=conf_count,
            uncertain_count=unc_count,
            unsupported_count=unsupp_count,
        )
