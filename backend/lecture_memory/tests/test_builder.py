"""Unit tests for LectureMemoryBuilder (Milestone 5)."""

import json
from pathlib import Path
import pytest

from lecture_memory.builder import LectureMemoryBuilder
from lecture_memory.schemas import LectureMemory
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


def test_1_empty_lecture_produces_valid_lecture_memory() -> None:
    """TEST 1: Empty lecture produces valid LectureMemory."""
    memory = LectureMemoryBuilder.build()
    assert isinstance(memory, LectureMemory)
    assert memory.schema_version == "1.0.0"
    assert len(memory.concepts) == 0
    assert len(memory.definitions) == 0
    assert len(memory.equations) == 0
    assert len(memory.important_points) == 0
    assert "No active pedagogical events" in memory.overview


def test_2_trusted_concept_enters_memory() -> None:
    """TEST 2: Trusted concept enters memory."""
    u = LectureUnderstanding(
        time_start=10.0,
        time_end=30.0,
        topic="Electromagnetic Induction",
        concepts=[
            Concept(
                name="Faraday's Law",
                explanation="EMF is induced by varying magnetic flux",
                timestamp_start=10.5,
                timestamp_end=28.0,
            )
        ],
        raw_transcript_ref="When magnetic flux changes, an EMF is induced.",
    )
    memory = LectureMemoryBuilder.build(understandings=[u])
    assert len(memory.concepts) == 1
    c = memory.concepts[0]
    assert c.id == "c1"
    assert c.name == "Faraday's Law"
    assert c.timestamp == 10.5
    assert c.provenance.source_type == "speech"


def test_3_trusted_definition_enters_memory() -> None:
    """TEST 3: Trusted definition enters memory."""
    u = LectureUnderstanding(
        time_start=5.0,
        time_end=15.0,
        topic="Electrostatics",
        definitions=[
            Definition(
                term="Electric Potential",
                definition="Work done per unit charge",
                timestamp=8.0,
            )
        ],
    )
    memory = LectureMemoryBuilder.build(understandings=[u])
    assert len(memory.definitions) == 1
    d = memory.definitions[0]
    assert d.term == "Electric Potential"
    assert d.timestamp == 8.0
    assert d.provenance.source_type == "speech"


def test_4_trusted_equation_enters_memory() -> None:
    """TEST 4: Trusted equation enters memory."""
    u = LectureUnderstanding(
        time_start=10.0,
        time_end=20.0,
        topic="Ohm's Law",
        equations=[
            Equation(
                latex_or_text="I = V / R",
                description="Ohm's Law",
                timestamp=12.5,
                grounding_status="supported",
                evidence_snippet="current is equal to voltage divided by resistance",
            )
        ],
    )
    memory = LectureMemoryBuilder.build(understandings=[u])
    assert len(memory.equations) == 1
    eq = memory.equations[0]
    assert eq.representation == "I = V / R"
    assert eq.grounding_status == "supported"
    assert eq.evidence_snippet == "current is equal to voltage divided by resistance"


def test_5_rejected_equation_does_not_enter_trusted_memory() -> None:
    """TEST 5: Rejected equation does NOT enter trusted memory."""
    u = LectureUnderstanding(
        time_start=0.0,
        time_end=25.0,
        topic="Faraday's Law",
        equations=[],  # Trusted equations empty because LLM proposal was hallucinated
        rejected_equations=[
            Equation(
                latex_or_text="EMF = - dPhi / dt",
                description="Hallucinated formula",
                timestamp=15.0,
                grounding_status="unsupported",
            )
        ],
    )
    memory = LectureMemoryBuilder.build(understandings=[u])
    # Trusted equations MUST NOT contain the rejected formula
    assert len(memory.equations) == 0
    # Preserved in rejected_equations for audit/debugging only
    assert len(memory.rejected_equations) == 1
    assert memory.rejected_equations[0].representation == "EMF = - dPhi / dt"
    assert memory.rejected_equations[0].grounding_status == "unsupported"


def test_6_important_point_preserves_timestamp() -> None:
    """TEST 6: Important point preserves timestamp."""
    u = LectureUnderstanding(
        time_start=40.0,
        time_end=60.0,
        topic="Thermodynamics",
        important_points=[
            ImportantPoint(
                point="Heat cannot spontaneously flow from colder to hotter body.",
                timestamp_start=42.5,
                timestamp_end=58.0,
            )
        ],
    )
    memory = LectureMemoryBuilder.build(understandings=[u])
    assert len(memory.important_points) == 1
    pt = memory.important_points[0]
    assert pt.timestamp == 42.5
    assert pt.provenance.timestamp_start == 42.5


def test_7_evidence_snippet_is_preserved() -> None:
    """TEST 7: Evidence snippet is preserved."""
    transcript_quote = "Remember that Lenz's law gives the direction of induced current."
    u = LectureUnderstanding(
        time_start=10.0,
        time_end=20.0,
        topic="Lenz's Law",
        concepts=[
            Concept(name="Lenz's Law", explanation="Opposition to flux change", timestamp_start=10.0, timestamp_end=20.0)
        ],
        raw_transcript_ref=transcript_quote,
    )
    memory = LectureMemoryBuilder.build(understandings=[u])
    assert memory.concepts[0].provenance.evidence_snippet == transcript_quote


def test_8_visual_event_becomes_visual_reference_without_invented_contents() -> None:
    """TEST 8: Visual event becomes a visual reference without invented contents."""
    u = LectureUnderstanding(
        time_start=0.0,
        time_end=15.0,
        topic="Optics",
        visual_references=[
            VisualReference(
                timestamp=5.0,
                source="camera",
                event_type="keyframe",
                frame_path="recordings/frames/lens.jpg",
                relevance="Instructor demonstrating convex lens on table.",
            )
        ],
    )
    memory = LectureMemoryBuilder.build(understandings=[u])
    assert len(memory.visual_references) == 1
    vr = memory.visual_references[0]
    assert vr.timestamp == 5.0
    assert vr.source == "Camera"
    assert vr.local_frame_reference == "recordings/frames/lens.jpg"
    assert vr.provenance.source_type == "visual"


def test_9_speech_and_visual_evidence_create_multimodal_reference() -> None:
    """TEST 9: Speech + visual evidence can create a multimodal reference."""
    timeline = LectureTimeline(
        lecture_id="session_multimodal",
        duration=30.0,
        synchronized_events=[
            SynchronizedEvent(
                start=10.0,
                end=20.0,
                speech=[SpeechEvent(start=10.0, end=18.0, text="Notice the waveform peaks on the oscilloscope.")],
                visual_events=[
                    VisualEvent(timestamp=12.0, source="screen", frame_path="/tmp/scope.jpg", change_score=0.4)
                ],
            )
        ],
    )
    memory = LectureMemoryBuilder.build(timeline=timeline)
    mm_events = [e for e in memory.timeline_events if e.type == "multimodal"]
    assert len(mm_events) == 1
    assert mm_events[0].timestamp == 10.0
    assert mm_events[0].provenance.source_type == "multimodal"


def test_10_raw_transcript_remains_unchanged() -> None:
    """TEST 10: Raw transcript remains unchanged."""
    raw = "Ekhane amra basically dekhchi je current ta increase korche because resistance komche."
    u = LectureUnderstanding(
        time_start=0.0,
        time_end=15.0,
        topic="Banglish Lecture",
        raw_transcript_ref=raw,
        concepts=[Concept(name="Current Dynamics", explanation="Current increases as resistance decreases", timestamp_start=0.0, timestamp_end=15.0)],
    )
    memory = LectureMemoryBuilder.build(understandings=[u])
    assert memory.concepts[0].provenance.evidence_snippet == raw


def test_11_missing_optional_timestamps_do_not_fabricate() -> None:
    """TEST 11: Missing optional timestamps do not cause fabricated timestamps."""
    u = LectureUnderstanding(
        time_start=0.0,
        time_end=10.0,
        topic="General Talk",
    )
    memory = LectureMemoryBuilder.build(understandings=[u])
    # Concepts list is empty; no timestamps fabricated
    assert len(memory.concepts) == 0


def test_15_two_identical_inputs_produce_deterministic_output() -> None:
    """TEST 15: Two identical inputs produce deterministic equivalent memory."""
    u = LectureUnderstanding(
        lecture_id="det_01",
        time_start=0.0,
        time_end=10.0,
        topic="Determinism Check",
        concepts=[Concept(name="Consistency", explanation="Same inputs give same outputs", timestamp_start=1.0, timestamp_end=5.0)],
    )
    m1 = LectureMemoryBuilder.build(understandings=[u], session_id="det_01", date="October 6, 2026", created_at="2026-10-06T12:00:00+00:00")
    m2 = LectureMemoryBuilder.build(understandings=[u], session_id="det_01", date="October 6, 2026", created_at="2026-10-06T12:00:00+00:00")

    assert m1.session_id == m2.session_id
    assert m1.title == m2.title
    assert m1.concepts[0].id == m2.concepts[0].id
    assert m1.overview == m2.overview
    assert m1.to_json() == m2.to_json()


def test_17_and_18_builder_offline_no_llm_or_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST 17 & 18: Memory builder does not invoke an LLM and does not require internet."""
    import socket
    # Disallow network sockets
    def block_socket(*args, **kwargs):
        raise RuntimeError("Network calls strictly forbidden in LectureMemoryBuilder!")
    monkeypatch.setattr(socket, "socket", block_socket)

    u = LectureUnderstanding(
        time_start=0.0,
        time_end=10.0,
        topic="Offline Test",
        concepts=[Concept(name="Offline Principle", explanation="Operates without cloud", timestamp_start=0.0, timestamp_end=10.0)],
    )
    memory = LectureMemoryBuilder.build(understandings=[u])
    assert memory.title == "Offline Test"
    assert memory.storage_local is True


def test_19_multilingual_unicode_support() -> None:
    """TEST 19: Unicode works correctly (English, Hindi, Banglish, Bengali Unicode)."""
    u_hindi = LectureUnderstanding(
        time_start=0.0,
        time_end=20.0,
        topic="विद्युत धारा (Electric Current)",
        concepts=[
            Concept(
                name="ओम का नियम (Ohm's Law)",
                explanation="धारा और विभवांतर का संबंध",
                timestamp_start=0.0,
                timestamp_end=10.0,
            )
        ],
    )
    u_bengali = LectureUnderstanding(
        time_start=20.0,
        time_end=40.0,
        topic="তড়িৎ প্রবাহ ও রোধ",
        concepts=[
            Concept(
                name="ওহমের সূত্র",
                explanation="তড়িৎ প্রবাহের পরিবর্তন রোধের ওপর নির্ভর করে",
                timestamp_start=20.0,
                timestamp_end=35.0,
            )
        ],
    )

    memory = LectureMemoryBuilder.build(understandings=[u_hindi, u_bengali], title="বহুভাষিক পাঠ (Multilingual Lecture)")
    assert memory.title == "বহুভাষিক পাঠ (Multilingual Lecture)"
    assert len(memory.concepts) == 2
    assert memory.concepts[0].name == "ओम का नियम (Ohm's Law)"
    assert memory.concepts[1].name == "ওহমের সূত্র"

    # Lossless JSON roundtrip with UTF-8
    json_bytes = memory.to_json().encode("utf-8")
    loaded = LectureMemory.from_json(json_bytes.decode("utf-8"))
    assert loaded.concepts[1].name == "ওহমের সূত্র"


def test_20_real_temporal_and_grounded_understanding_integration() -> None:
    """TEST 20: Real existing temporal + understanding/grounding output converted to LectureMemory."""
    # Build temporal timeline
    timeline = LectureTimeline(
        lecture_id="real_test_session_01",
        duration=14.84,
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
                data={"timestamp": 5.0, "frame_path": "recordings/frames/frame_001.jpg", "change_score": 0.45},
            ),
        ],
        synchronized_events=[
            SynchronizedEvent(
                start=2.0,
                end=13.51,
                speech=[
                    SpeechEvent(
                        start=2.0,
                        end=13.51,
                        text="HALLO HALLO, AAMAN NAM AUDRISHMAR GANAR JEE, AAMI IT SECOND YEAR E PARASUNA KORI.",
                        language=["bn", "en"],
                    )
                ],
                visual_events=[
                    VisualEvent(timestamp=5.0, source="camera", frame_path="recordings/frames/frame_001.jpg", change_score=0.45)
                ],
            )
        ],
        total_speech_events=1,
        total_visual_events=1,
    )

    # Real grounded understanding output
    understanding = LectureUnderstanding(
        lecture_id="real_test_session_01",
        time_start=2.0,
        time_end=13.51,
        topic="Introduction and Personal Details",
        concepts=[
            Concept(
                name="Introduction to speaker",
                explanation="The speaker introduces themselves as Aman, a second-year IT student.",
                timestamp_start=2.0,
                timestamp_end=13.51,
            )
        ],
        definitions=[
            Definition(
                term="Parasun",
                definition="A subject or course of study",
                timestamp=13.51,
            )
        ],
        equations=[],
        rejected_equations=[],
        important_points=[
            ImportantPoint(
                point="The speaker is an IT second-year student.",
                timestamp_start=2.0,
                timestamp_end=13.51,
            )
        ],
        visual_references=[
            VisualReference(
                timestamp=5.0,
                source="camera",
                event_type="keyframe",
                frame_path="recordings/frames/frame_001.jpg",
                relevance="Speaker's introduction with camera keyframe",
            )
        ],
        confidence=0.9,
        grounding_score=1.0,
        raw_transcript_ref="HALLO HALLO, AAMAN NAM AUDRISHMAR GANAR JEE, AAMI IT SECOND YEAR E PARASUNA KORI.",
    )

    memory = LectureMemoryBuilder.build(
        timeline=timeline,
        understandings=[understanding],
        subject="Computer Science",
    )

    assert memory.session_id == "real_test_session_01"
    assert memory.subject == "Computer Science"
    assert memory.title == "Introduction and Personal Details"
    assert len(memory.concepts) == 1
    assert len(memory.definitions) == 1
    assert len(memory.equations) == 0
    assert len(memory.visual_references) == 1
    assert len(memory.timeline_events) >= 3  # speech + visual + multimodal + concept milestone
    assert memory.grounding_summary["overall_grounding_score"] == 1.0
