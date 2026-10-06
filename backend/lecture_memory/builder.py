"""Builder module for GyanDrishti Canonical Lecture Memory (Milestone 5).

Deterministically assembles temporal streams and grounded understandings into
a canonical, immutable, evidence-grounded LectureMemory instance.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Union

from temporal_engine.schemas import LectureTimeline, SynchronizedEvent
from understanding_engine.schemas import LectureUnderstanding

from .provenance import (
    Provenance,
    create_derived_provenance,
    create_multimodal_provenance,
    create_speech_provenance,
    create_visual_provenance,
)
from .schemas import (
    LectureMemory,
    LectureMetadata,
    MemoryConcept,
    MemoryDefinition,
    MemoryEquation,
    MemoryImportantPoint,
    MemoryQuestionCandidate,
    MemoryTimelineEvent,
    MemoryVisualReference,
)

logger = logging.getLogger(__name__)


class LectureMemoryBuilder:
    """Constructs canonical, evidence-grounded LectureMemory representations.

    Follows strict determinism:
    - Zero LLM invocation
    - Zero network or cloud calls
    - Admittance only of verified items; rejected items never enter trusted facts.
    """

    @classmethod
    def build(
        cls,
        timeline: Optional[LectureTimeline] = None,
        understandings: Optional[List[LectureUnderstanding]] = None,
        session_id: Optional[str] = None,
        title: Optional[str] = None,
        subject: Optional[str] = None,
        date: Optional[str] = None,
        created_at: Optional[str] = None,
        visual_analysis: Optional[Union[List[Any], Dict[str, Any]]] = None,
    ) -> LectureMemory:
        """Builds a canonical LectureMemory instance from timeline and understanding evidence.

        Args:
            timeline: Multimodal synchronized lecture timeline from temporal engine.
            understandings: Grounded lecture understandings from understanding engine.
            session_id: Explicit session ID, or inferred from timeline/understanding.
            title: Explicit lecture title, or synthesized from topic understandings.
            subject: Academic subject, defaults to 'General Lecture'.
            date: Display date string.
        """
        understandings = understandings or []

        # 1. Resolve Session ID
        effective_session_id = (
            session_id
            or (timeline.lecture_id if timeline else None)
            or (understandings[0].lecture_id if understandings and understandings[0].lecture_id else None)
            or f"lecture_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        )

        # 2. Compute Duration and Ingestion Metadata
        duration = 0.0
        languages_detected: Set[str] = set()
        scripts_detected: Set[str] = set()
        total_speech_segments = 0
        total_visual_events = 0
        recordings_map: Dict[str, str] = {}

        if timeline:
            duration = max(duration, timeline.duration)
            total_speech_segments = timeline.total_speech_events
            total_visual_events = timeline.total_visual_events
            for se in timeline.synchronized_events:
                for sp in se.speech:
                    languages_detected.update(sp.language)
                    if sp.script:
                        scripts_detected.update(sp.script)

        for u in understandings:
            duration = max(duration, u.time_end)

        # 3. Extract Concepts with Strict Provenance
        concepts: List[MemoryConcept] = []
        concept_idx = 1
        seen_concept_names: Set[str] = set()

        for u in understandings:
            for c in u.concepts:
                c_key = c.name.strip().lower()
                if c_key in seen_concept_names:
                    continue
                seen_concept_names.add(c_key)

                prov = create_speech_provenance(
                    start=c.timestamp_start,
                    end=c.timestamp_end,
                    text_snippet=u.raw_transcript_ref or c.explanation,
                    source_id=effective_session_id,
                )

                concepts.append(
                    MemoryConcept(
                        id=f"c{concept_idx}",
                        name=c.name.strip(),
                        explanation=c.explanation.strip(),
                        timestamp=c.timestamp_start,
                        timestamp_start=c.timestamp_start,
                        timestamp_end=c.timestamp_end,
                        provenance=prov,
                    )
                )
                concept_idx += 1

        # 4. Extract Definitions with Strict Provenance
        definitions: List[MemoryDefinition] = []
        seen_def_terms: Set[str] = set()

        for u in understandings:
            for d in u.definitions:
                d_key = d.term.strip().lower()
                if d_key in seen_def_terms:
                    continue
                seen_def_terms.add(d_key)

                prov = create_speech_provenance(
                    start=d.timestamp,
                    end=d.timestamp,
                    text_snippet=d.definition,
                    source_id=effective_session_id,
                )

                definitions.append(
                    MemoryDefinition(
                        term=d.term.strip(),
                        definition=d.definition.strip(),
                        timestamp=d.timestamp,
                        provenance=prov,
                    )
                )

        # 5. Extract Equations (CRITICAL: Trusted Only)
        trusted_equations: List[MemoryEquation] = []
        rejected_equations: List[MemoryEquation] = []
        seen_eqs: Set[str] = set()

        for u in understandings:
            # Trusted equations (passed deterministic grounding)
            for eq in u.equations:
                eq_key = eq.latex_or_text.strip().lower()
                if eq_key in seen_eqs:
                    continue
                seen_eqs.add(eq_key)

                prov = create_speech_provenance(
                    start=eq.timestamp,
                    end=eq.timestamp,
                    text_snippet=eq.evidence_snippet or u.raw_transcript_ref or eq.latex_or_text,
                    source_id=effective_session_id,
                    grounding_status="supported",
                )

                trusted_equations.append(
                    MemoryEquation(
                        name=eq.description.strip() or "Mathematical Formulation",
                        representation=eq.latex_or_text.strip(),
                        explanation=eq.description.strip() or "Verified mathematically from lecture speech.",
                        timestamp=eq.timestamp,
                        grounding_status="supported",
                        evidence_snippet=eq.evidence_snippet,
                        provenance=prov,
                    )
                )

            # Rejected equations (for audit/debugging only; NEVER exposed in trusted facts)
            for req in u.rejected_equations:
                prov_rej = create_derived_provenance(
                    start=req.timestamp,
                    end=req.timestamp,
                    evidence_snippet=f"Rejected hallucination: {req.latex_or_text}",
                    grounding_status="unsupported",
                )
                rejected_equations.append(
                    MemoryEquation(
                        name=req.description.strip() or "Rejected Formula",
                        representation=req.latex_or_text.strip(),
                        explanation="Proposed by LLM but rejected by deterministic evidence grounding.",
                        timestamp=req.timestamp,
                        grounding_status="unsupported",
                        evidence_snippet=None,
                        provenance=prov_rej,
                    )
                )

        # 6. Extract Important Points
        important_points: List[MemoryImportantPoint] = []
        seen_points: Set[str] = set()

        for u in understandings:
            for pt in u.important_points:
                pt_key = pt.point.strip().lower()
                if pt_key in seen_points:
                    continue
                seen_points.add(pt_key)

                prov = create_speech_provenance(
                    start=pt.timestamp_start,
                    end=pt.timestamp_end,
                    text_snippet=u.raw_transcript_ref or pt.point,
                    source_id=effective_session_id,
                    grounding_status="supported" if pt.importance != "uncertain" else "uncertain",
                )

                important_points.append(
                    MemoryImportantPoint(
                        point=pt.point.strip(),
                        timestamp=pt.timestamp_start,
                        importance=pt.importance,
                        provenance=prov,
                    )
                )

        # 7. Extract Visual References (No Fabricated Contents)
        visual_references: List[MemoryVisualReference] = []
        seen_visual_paths: Set[str] = set()

        # Index visual analysis results if provided
        visual_analysis_by_key: Dict[str, Any] = {}
        if visual_analysis:
            if isinstance(visual_analysis, dict):
                for k, v in visual_analysis.items():
                    visual_analysis_by_key[k] = v
                    src_img = getattr(v, "source_image", None) or (v.get("source_image") if isinstance(v, dict) else None)
                    kf_id = getattr(v, "keyframe_id", None) or (v.get("keyframe_id") if isinstance(v, dict) else None)
                    if src_img:
                        visual_analysis_by_key[src_img] = v
                        visual_analysis_by_key[os.path.basename(src_img)] = v
                    if kf_id:
                        visual_analysis_by_key[kf_id] = v
            elif isinstance(visual_analysis, list):
                for v in visual_analysis:
                    kf_id = getattr(v, "keyframe_id", None) or (v.get("keyframe_id") if isinstance(v, dict) else None)
                    src_img = getattr(v, "source_image", None) or (v.get("source_image") if isinstance(v, dict) else None)
                    if kf_id:
                        visual_analysis_by_key[kf_id] = v
                    if src_img:
                        visual_analysis_by_key[src_img] = v
                        visual_analysis_by_key[os.path.basename(src_img)] = v

        for u in understandings:
            for vr in u.visual_references:
                v_key = f"{vr.frame_path or ''}_{vr.timestamp}"
                if v_key in seen_visual_paths:
                    continue
                seen_visual_paths.add(v_key)

                prov = create_visual_provenance(
                    timestamp=vr.timestamp,
                    frame_path=vr.frame_path or "unspecified_frame",
                    event_type=vr.event_type,
                )

                frame_ref = vr.frame_path or ""
                kf_id_guess = os.path.splitext(os.path.basename(frame_ref))[0] if frame_ref else None
                matched_ocr = (
                    visual_analysis_by_key.get(frame_ref)
                    or visual_analysis_by_key.get(os.path.basename(frame_ref))
                    or (visual_analysis_by_key.get(kf_id_guess) if kf_id_guess else None)
                )

                extracted_text = None
                ocr_conf = None
                ocr_status = "ocr_pending"
                pot_eqs = []

                if matched_ocr:
                    extracted_text = (
                        getattr(matched_ocr, "raw_text_combined", None)
                        or (matched_ocr.get("raw_text_combined") if isinstance(matched_ocr, dict) else None)
                    )
                    ocr_conf = (
                        getattr(matched_ocr, "overall_confidence", None)
                        if hasattr(matched_ocr, "overall_confidence")
                        else (matched_ocr.get("overall_confidence") if isinstance(matched_ocr, dict) else None)
                    )
                    status_val = (
                        getattr(matched_ocr, "processing_status", "ocr_pending")
                        if hasattr(matched_ocr, "processing_status")
                        else (matched_ocr.get("processing_status", "ocr_pending") if isinstance(matched_ocr, dict) else "ocr_pending")
                    )
                    ocr_status = status_val.value if hasattr(status_val, "value") else str(status_val)
                    pot_eqs = (
                        getattr(matched_ocr, "potential_equations", [])
                        if hasattr(matched_ocr, "potential_equations")
                        else (matched_ocr.get("potential_equations", []) if isinstance(matched_ocr, dict) else [])
                    )

                visual_references.append(
                    MemoryVisualReference(
                        timestamp=vr.timestamp,
                        source=vr.source.title(),
                        event_type=vr.event_type.replace("_", " ").title(),
                        local_frame_reference=vr.frame_path or f"Frame at {vr.timestamp:.1f}s",
                        description=vr.relevance,
                        keyframe_id=kf_id_guess,
                        extracted_text=extracted_text,
                        ocr_confidence=ocr_conf,
                        ocr_status=ocr_status,
                        potential_equations=pot_eqs,
                        provenance=prov,
                    )
                )

        # Also ingest any keyframes present in timeline that were not in understandings
        if timeline:
            for kf_evt in timeline.get_keyframes():
                v_key = f"{kf_evt.frame_path}_{kf_evt.timestamp}"
                if v_key in seen_visual_paths:
                    continue
                seen_visual_paths.add(v_key)

                prov = create_visual_provenance(
                    timestamp=kf_evt.timestamp,
                    frame_path=kf_evt.frame_path,
                    event_type=kf_evt.type,
                )

                frame_ref = kf_evt.frame_path
                kf_id_guess = os.path.splitext(os.path.basename(frame_ref))[0]
                matched_ocr = (
                    visual_analysis_by_key.get(frame_ref)
                    or visual_analysis_by_key.get(os.path.basename(frame_ref))
                    or visual_analysis_by_key.get(kf_id_guess)
                )

                extracted_text = None
                ocr_conf = None
                ocr_status = "ocr_pending"
                pot_eqs = []

                if matched_ocr:
                    extracted_text = (
                        getattr(matched_ocr, "raw_text_combined", None)
                        or (matched_ocr.get("raw_text_combined") if isinstance(matched_ocr, dict) else None)
                    )
                    ocr_conf = (
                        getattr(matched_ocr, "overall_confidence", None)
                        if hasattr(matched_ocr, "overall_confidence")
                        else (matched_ocr.get("overall_confidence") if isinstance(matched_ocr, dict) else None)
                    )
                    status_val = (
                        getattr(matched_ocr, "processing_status", "ocr_pending")
                        if hasattr(matched_ocr, "processing_status")
                        else (matched_ocr.get("processing_status", "ocr_pending") if isinstance(matched_ocr, dict) else "ocr_pending")
                    )
                    ocr_status = status_val.value if hasattr(status_val, "value") else str(status_val)
                    pot_eqs = (
                        getattr(matched_ocr, "potential_equations", [])
                        if hasattr(matched_ocr, "potential_equations")
                        else (matched_ocr.get("potential_equations", []) if isinstance(matched_ocr, dict) else [])
                    )

                visual_references.append(
                    MemoryVisualReference(
                        timestamp=kf_evt.timestamp,
                        source=kf_evt.source.title(),
                        event_type=kf_evt.type.replace("_", " ").title(),
                        local_frame_reference=frame_ref,
                        description="Keyframe captured from lecture visual stream",
                        keyframe_id=kf_id_guess,
                        extracted_text=extracted_text,
                        ocr_confidence=ocr_conf,
                        ocr_status=ocr_status,
                        potential_equations=pot_eqs,
                        provenance=prov,
                    )
                )

        # 8. Extract Revision Questions
        questions: List[MemoryQuestionCandidate] = []
        seen_questions: Set[str] = set()

        for u in understandings:
            for q in u.question_candidates:
                q_key = q.question.strip().lower()
                if q_key in seen_questions:
                    continue
                seen_questions.add(q_key)

                prov = create_derived_provenance(
                    start=q.relevant_timestamp,
                    end=q.relevant_timestamp,
                    evidence_snippet=q.expected_answer or q.question,
                )

                questions.append(
                    MemoryQuestionCandidate(
                        question=q.question.strip(),
                        answer=q.expected_answer.strip() if q.expected_answer else "Refer to lecture discussion.",
                        difficulty=q.difficulty,
                        timestamp=q.relevant_timestamp,
                        provenance=prov,
                    )
                )

        # 9. Assemble Chronological Timeline Events
        timeline_events: List[MemoryTimelineEvent] = []

        if timeline:
            if timeline.chronological_stream:
                # Populate from timeline stream
                for te in timeline.chronological_stream:
                    if te.type == "speech":
                        speech_text = te.data.get("text", "").strip()
                        prov_te = create_speech_provenance(
                            start=te.timestamp,
                            end=te.data.get("end", te.timestamp),
                            text_snippet=speech_text,
                        )
                        timeline_events.append(
                            MemoryTimelineEvent(
                                timestamp=te.timestamp,
                                type="speech",
                                label="Speech",
                                details=speech_text if len(speech_text) <= 120 else speech_text[:117] + "...",
                                provenance=prov_te,
                            )
                        )
                    elif te.type in ("visual_change", "keyframe"):
                        frame_p = te.data.get("frame_path", "")
                        prov_ve = create_visual_provenance(
                            timestamp=te.timestamp,
                            frame_path=frame_p,
                            event_type=te.type,
                        )
                        timeline_events.append(
                            MemoryTimelineEvent(
                                timestamp=te.timestamp,
                                type="visual",
                                label="Visual Change" if te.type == "visual_change" else "Keyframe",
                                details=f"Frame captured ({te.source}): {frame_p}",
                                provenance=prov_ve,
                            )
                        )

            # Add multimodal clusters if speech and visual co-occurred
            for se in timeline.synchronized_events:
                if se.speech and se.visual_events:
                    sp_summary = se.speech[0].text[:80] if se.speech else ""
                    prov_mm = create_multimodal_provenance(
                        start=se.start,
                        end=se.end,
                        speech_snippet=sp_summary,
                        frame_path=se.visual_events[0].frame_path,
                    )
                    timeline_events.append(
                        MemoryTimelineEvent(
                            timestamp=se.start,
                            type="multimodal",
                            label="Multimodal",
                            details=f"Instructor speech synchronized with board/slide activity.",
                            provenance=prov_mm,
                        )
                    )

        # Inject concept and equation milestone markers into timeline
        for c in concepts:
            timeline_events.append(
                MemoryTimelineEvent(
                    timestamp=c.timestamp,
                    type="concept",
                    label="Important concept",
                    details=f"{c.name}: {c.explanation[:100]}...",
                    provenance=c.provenance,
                )
            )

        for eq in trusted_equations:
            timeline_events.append(
                MemoryTimelineEvent(
                    timestamp=eq.timestamp,
                    type="equation",
                    label="Equation",
                    details=f"{eq.name} ({eq.representation})",
                    provenance=eq.provenance,
                )
            )

        # Sort timeline events strictly chronologically
        timeline_events.sort(key=lambda e: (e.timestamp, e.type))

        # 10. Synthesize Grounded Title and Overview
        all_topics = [u.topic.strip() for u in understandings if u.topic and u.topic != "Lecture Segment"]
        effective_title = title or (all_topics[0] if all_topics else "Lecture Session")

        if concepts:
            overview_lines = [
                f"This lecture covers foundational concepts including {', '.join(c.name for c in concepts[:4])}."
            ]
            if trusted_equations:
                overview_lines.append(
                    f"Core mathematical relationships verified: {', '.join(eq.representation for eq in trusted_equations)}."
                )
            if important_points:
                overview_lines.append(
                    f"Key pedagogical takeaways focus on {important_points[0].point.lower()}."
                )
            overview = " ".join(overview_lines)
        elif understandings and understandings[0].topic:
            overview = f"Lecture session addressing {understandings[0].topic}."
        else:
            overview = "No active pedagogical events recorded in this lecture session."

        # 11. Calculate Grounding Summary Metrics
        grounding_scores = [u.grounding_score for u in understandings if hasattr(u, "grounding_score")]
        avg_grounding_score = (
            round(sum(grounding_scores) / len(grounding_scores), 2)
            if grounding_scores
            else 1.0
        )

        grounding_summary = {
            "overall_grounding_score": avg_grounding_score,
            "trusted_equations_count": len(trusted_equations),
            "rejected_equations_count": len(rejected_equations),
            "total_concepts": len(concepts),
            "total_definitions": len(definitions),
            "total_important_points": len(important_points),
            "total_visual_references": len(visual_references),
        }

        # 12. Build Metadata Model
        metadata = LectureMetadata(
            subject=subject or "General Lecture",
            language_summary=sorted(list(languages_detected)),
            scripts_summary=sorted(list(scripts_detected)),
            total_speech_segments=total_speech_segments,
            total_visual_events=total_visual_events,
            source_recordings=recordings_map,
        )

        return LectureMemory(
            schema_version="1.0.0",
            session_id=effective_session_id,
            title=effective_title,
            subject=subject or "General Lecture",
            date=date or datetime.now(timezone.utc).strftime("%B %d, %Y"),
            created_at=created_at or datetime.now(timezone.utc).isoformat(),
            duration=round(duration, 2),
            storage_local=True,
            overview=overview,
            timeline_events=timeline_events,
            concepts=concepts,
            definitions=definitions,
            equations=trusted_equations,
            rejected_equations=rejected_equations,
            important_points=important_points,
            visual_references=visual_references,
            revision_questions=questions,
            metadata=metadata,
            grounding_summary=grounding_summary,
        )
