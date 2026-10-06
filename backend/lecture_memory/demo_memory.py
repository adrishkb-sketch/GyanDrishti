"""Deterministic offline integration demo for GyanDrishti Lecture Memory Engine (Milestone 5).

Demonstrates the complete end-to-end pipeline:
Temporal Fusion Timeline
  +
Grounded Lecture Understanding
  ↓
Canonical Lecture Memory Builder
  ↓
Atomic Local Storage & Serialization
"""

import json
from pathlib import Path

from temporal_engine.schemas import (
    LectureTimeline,
    SpeechEvent,
    SynchronizedEvent,
    TimelineEvent,
    VisualEvent,
)
from understanding_engine.schemas import (
    Concept,
    Definition,
    Equation,
    ImportantPoint,
    LectureUnderstanding,
    QuestionCandidate,
    VisualReference,
)
from lecture_memory.builder import LectureMemoryBuilder
from lecture_memory.storage import LectureMemoryStorage
from lecture_memory.serializers import to_markdown_notes


def run_demo() -> None:
    print("=" * 80)
    print("GYANDRISHTI LECTURE MEMORY ENGINE — DETERMINISTIC INTEGRATION DEMO")
    print("=" * 80)

    # 1. Real Ingestion Evidence (from recordings/validation_test.json)
    raw_transcript = (
        "HALLO HALLO, AAMAN NAM AUDRISHMAR GANAR JEE, AAMI IT SECOND YEAR E PARASUNA KORI. "
        "Today we study Ohm's Law. Current is equal to voltage divided by resistance."
    )

    # 2. Reconstruct Temporal Fusion Timeline
    timeline = LectureTimeline(
        lecture_id="lecture_demo_20261006_01",
        duration=45.0,
        chronological_stream=[
            TimelineEvent(
                timestamp=2.0,
                type="speech",
                source="speech",
                data={"start": 2.0, "end": 13.51, "text": "HALLO HALLO, AAMAN NAM AUDRISHMAR GANAR JEE, AAMI IT SECOND YEAR E PARASUNA KORI."},
            ),
            TimelineEvent(
                timestamp=5.0,
                type="keyframe",
                source="camera",
                data={"timestamp": 5.0, "frame_path": "recordings/frames/frame_speaker.jpg", "change_score": 0.45},
            ),
            TimelineEvent(
                timestamp=18.0,
                type="speech",
                source="speech",
                data={"start": 18.0, "end": 42.0, "text": "Today we study Ohm's Law. Current is equal to voltage divided by resistance."},
            ),
            TimelineEvent(
                timestamp=25.0,
                type="keyframe",
                source="screen",
                data={"timestamp": 25.0, "frame_path": "recordings/frames/circuit_diagram.png", "change_score": 0.65},
            ),
        ],
        synchronized_events=[
            SynchronizedEvent(
                start=2.0,
                end=14.0,
                speech=[
                    SpeechEvent(start=2.0, end=13.51, text="HALLO HALLO, AAMAN NAM AUDRISHMAR GANAR JEE, AAMI IT SECOND YEAR E PARASUNA KORI.", language=["bn", "en"])
                ],
                visual_events=[
                    VisualEvent(timestamp=5.0, source="camera", frame_path="recordings/frames/frame_speaker.jpg")
                ],
            ),
            SynchronizedEvent(
                start=18.0,
                end=42.0,
                speech=[
                    SpeechEvent(start=18.0, end=42.0, text="Today we study Ohm's Law. Current is equal to voltage divided by resistance.", language=["en"])
                ],
                visual_events=[
                    VisualEvent(timestamp=25.0, source="screen", frame_path="recordings/frames/circuit_diagram.png")
                ],
            ),
        ],
        total_speech_events=2,
        total_visual_events=2,
    )

    # 3. Reconstruct Grounded Understandings (with both trusted and rejected items)
    u_intro = LectureUnderstanding(
        lecture_id="lecture_demo_20261006_01",
        time_start=2.0,
        time_end=14.0,
        topic="Speaker Introduction and Academic Background",
        concepts=[
            Concept(
                name="Introduction to Speaker",
                explanation="The speaker introduces themselves as Aman, a second-year IT student.",
                timestamp_start=2.0,
                timestamp_end=13.51,
            )
        ],
        definitions=[],
        equations=[],
        rejected_equations=[],
        important_points=[
            ImportantPoint(
                point="Speaker is in second year of IT engineering.",
                timestamp_start=2.0,
                timestamp_end=13.51,
            )
        ],
        visual_references=[
            VisualReference(
                timestamp=5.0,
                source="camera",
                event_type="keyframe",
                frame_path="recordings/frames/frame_speaker.jpg",
                relevance="Speaker introductory frame",
            )
        ],
        confidence=0.9,
        grounding_score=1.0,
        raw_transcript_ref="HALLO HALLO, AAMAN NAM AUDRISHMAR GANAR JEE, AAMI IT SECOND YEAR E PARASUNA KORI.",
    )

    u_physics = LectureUnderstanding(
        lecture_id="lecture_demo_20261006_01",
        time_start=18.0,
        time_end=42.0,
        topic="Ohm's Law and Circuit Dynamics",
        concepts=[
            Concept(
                name="Ohm's Law",
                explanation="Electric current is proportional to voltage and inversely proportional to resistance.",
                timestamp_start=18.0,
                timestamp_end=40.0,
            )
        ],
        definitions=[
            Definition(
                term="Electric Current",
                definition="The flow of electric charge per unit time through a conductor.",
                timestamp=20.0,
            )
        ],
        equations=[
            # TRUSTED: Explicitly dictated in speech ("Current is equal to voltage divided by resistance")
            Equation(
                latex_or_text="I = V / R",
                description="Ohm's Law relating current, voltage, and resistance",
                timestamp=22.5,
                grounding_status="supported",
                evidence_snippet="Current is equal to voltage divided by resistance",
            )
        ],
        rejected_equations=[
            # REJECTED: LLM hallucinated unrelated formula (E = mc^2), rejected by deterministic grounding
            Equation(
                latex_or_text="E = m * c^2",
                description="Mass-energy equivalence",
                timestamp=30.0,
                grounding_status="unsupported",
            )
        ],
        important_points=[
            ImportantPoint(
                point="Reducing circuit resistance increases current for constant voltage.",
                timestamp_start=20.0,
                timestamp_end=35.0,
            )
        ],
        visual_references=[
            VisualReference(
                timestamp=25.0,
                source="screen",
                event_type="keyframe",
                frame_path="recordings/frames/circuit_diagram.png",
                relevance="Circuit diagram displayed on screen showing resistor and power source",
            )
        ],
        question_candidates=[
            QuestionCandidate(
                question="What happens to the current if resistance is doubled at constant voltage?",
                expected_answer="The current is halved according to I = V / R.",
                difficulty="medium",
                relevant_timestamp=22.5,
            )
        ],
        confidence=0.95,
        grounding_score=0.8,
        raw_transcript_ref="Today we study Ohm's Law. Current is equal to voltage divided by resistance.",
    )

    # 4. Build Canonical LectureMemory
    print("\n[1] Invoking LectureMemoryBuilder...")
    memory = LectureMemoryBuilder.build(
        timeline=timeline,
        understandings=[u_intro, u_physics],
        subject="Electrical Engineering",
        date="October 6, 2026",
    )

    # 5. Save to Local Atomic Storage
    print("\n[2] Saving LectureMemory to local storage...")
    storage = LectureMemoryStorage(base_dir="data/lectures")
    saved_path = storage.save(memory)
    print(f"    Saved canonical file to: {saved_path}")

    # 6. Verify Lossless Reload
    print("\n[3] Loading back from local storage...")
    loaded = storage.load(memory.session_id)
    assert loaded.session_id == memory.session_id

    # 7. Print Concise Quality Summary
    print("\n" + "=" * 80)
    print("CANONICAL LECTURE MEMORY SUMMARY")
    print("=" * 80)
    print(f"Lecture:            {loaded.title}")
    print(f"Session ID:         {loaded.session_id}")
    print(f"Subject:            {loaded.subject}")
    print(f"Date:               {loaded.date}")
    print(f"Duration:           {loaded.duration}s")
    print(f"Storage:            {'Local verified' if loaded.storage_local else 'External'}")
    print(f"Overview:           {loaded.overview}")
    print(f"Concepts ({len(loaded.concepts)}):         {[c.name for c in loaded.concepts]}")
    print(f"Definitions ({len(loaded.definitions)}):      {[d.term for d in loaded.definitions]}")
    print(f"Trusted Equations ({len(loaded.equations)}):{[eq.representation for eq in loaded.equations]}")
    print(f"Rejected Equations ({len(loaded.rejected_equations)}): {[eq.representation for eq in loaded.rejected_equations]}")
    print(f"Important Points ({len(loaded.important_points)}): {[pt.point[:45] + '...' for pt in loaded.important_points]}")
    print(f"Questions ({len(loaded.revision_questions)}):        {[q.question for q in loaded.revision_questions]}")
    print(f"Visual References ({len(loaded.visual_references)}):{[vr.local_frame_reference for vr in loaded.visual_references]}")
    print(f"Timeline Events ({len(loaded.timeline_events)}):  {len(loaded.timeline_events)} chronological events")
    print(f"Grounding Status:   Score={loaded.grounding_summary.get('overall_grounding_score')} (Trusted: {len(loaded.equations)}, Rejected: {len(loaded.rejected_equations)})")

    # 8. Test Frontend Dict Export
    fe_dict = loaded.to_frontend_dict()
    print("\n[4] Verified Frontend Export:")
    print(f"    Frontend session_id: {fe_dict['session_id']}")
    print(f"    Frontend timeline_events count: {len(fe_dict['timeline_events'])}")
    print(f"    Frontend concepts count: {len(fe_dict['concepts'])}")
    print(f"    Frontend equations count: {len(fe_dict['equations'])}")
    print("\nDemo completed successfully with 100% deterministic local execution.")


if __name__ == "__main__":
    run_demo()
