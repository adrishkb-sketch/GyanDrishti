"""Unit tests for LectureUnderstandingEngine analyzer module."""

import pytest
from understanding_engine.analyzer import LectureUnderstandingEngine
from understanding_engine.llm import MockLLMProvider


def test_analyzer_banglish_transcript_semantic_understanding() -> None:
    banglish_text = "Ekhane amra basically dekhchi je current ta increase korche because resistance komche, so I is equal to V divided by R."

    # Mock response illustrating semantic understanding of Banglish speech
    def mock_banglish_response(prompt: str) -> str:
        assert banglish_text in prompt
        return """{
            "topic": "Current and Resistance Relationship",
            "concepts": [
                {
                    "name": "Current-Resistance Inverse Relationship",
                    "explanation": "Current increases when resistance decreases under constant voltage.",
                    "timestamp_start": 120.0,
                    "timestamp_end": 145.0
                }
            ],
            "definitions": [],
            "equations": [
                {
                    "latex_or_text": "I = V / R",
                    "description": "Ohm's Law expressing current as inversely proportional to resistance",
                    "timestamp": 125.0,
                    "explicitly_spoken": true
                }
            ],
            "important_points": [
                {
                    "point": "Current increases when resistance decreases under constant voltage.",
                    "timestamp_start": 120.0,
                    "timestamp_end": 145.0,
                    "importance": "high"
                }
            ],
            "visual_references": [
                {
                    "timestamp": 122.4,
                    "source": "camera",
                    "event_type": "keyframe",
                    "frame_path": "frames/circuit.jpg",
                    "relevance": "Teacher pointing to board diagram while explaining current change."
                }
            ],
            "question_candidates": [
                {
                    "question": "What happens to the current in a circuit when resistance decreases?",
                    "expected_answer": "The current increases.",
                    "difficulty": "easy",
                    "relevant_timestamp": 122.0
                }
            ],
            "confidence": 0.95
        }"""

    provider = MockLLMProvider(response_generator=mock_banglish_response)
    engine = LectureUnderstandingEngine(provider=provider)

    speech_segments = [
        {"start": 120.0, "end": 145.0, "text": banglish_text, "language": ["bn", "en"]}
    ]
    visual_events = [
        {"timestamp": 122.4, "source": "camera", "type": "keyframe", "frame_path": "frames/circuit.jpg"}
    ]

    understanding = engine.analyze_block(
        start_time=120.0,
        end_time=145.0,
        speech_segments=speech_segments,
        visual_events=visual_events,
        lecture_id="lec_banglish_01",
    )

    # Verify understanding fields
    assert understanding.topic == "Current and Resistance Relationship"
    assert len(understanding.concepts) == 1
    assert understanding.concepts[0].name == "Current-Resistance Inverse Relationship"
    assert len(understanding.equations) == 1
    assert understanding.equations[0].latex_or_text == "I = V / R"
    assert len(understanding.visual_references) == 1
    assert understanding.visual_references[0].source == "camera"

    # CRITICAL: Verify raw source transcript was preserved strictly untouched
    assert understanding.raw_transcript_ref == banglish_text


def test_analyzer_multilingual_hindi_english() -> None:
    hindi_text = "अब हम Faraday के law के बारे में पढ़ेंगे। जब magnetic flux change होता है तब EMF induce होता है।"

    def mock_hindi_response(prompt: str) -> str:
        assert "Faraday" in prompt
        return """{
            "topic": "Faraday's Law of Electromagnetic Induction",
            "concepts": [
                {
                    "name": "Electromagnetic Induction",
                    "explanation": "Changing magnetic flux over time induces an electromotive force (EMF).",
                    "timestamp_start": 50.0,
                    "timestamp_end": 75.0
                }
            ],
            "definitions": [
                {
                    "term": "EMF",
                    "definition": "Induced electromotive force resulting from magnetic flux variation.",
                    "timestamp": 55.0
                }
            ],
            "equations": [
                {
                    "latex_or_text": "EMF = - dPhi / dt",
                    "description": "Faraday's Law of Induction",
                    "timestamp": 60.0,
                    "explicitly_spoken": true
                }
            ],
            "important_points": [
                {
                    "point": "Induced EMF is proportional to rate of change of magnetic flux.",
                    "timestamp_start": 50.0,
                    "timestamp_end": 75.0,
                    "importance": "high"
                }
            ],
            "visual_references": [],
            "question_candidates": [],
            "confidence": 0.98
        }"""

    provider = MockLLMProvider(response_generator=mock_hindi_response)
    engine = LectureUnderstandingEngine(provider=provider)

    speech_segments = [{"start": 50.0, "end": 75.0, "text": hindi_text, "language": ["hi", "en"]}]
    understanding = engine.analyze_block(50.0, 75.0, speech_segments, [], lecture_id="lec_hi")

    assert understanding.topic == "Faraday's Law of Electromagnetic Induction"
    assert len(understanding.definitions) == 1
    assert understanding.definitions[0].term == "EMF"
    assert understanding.raw_transcript_ref == hindi_text


def test_analyzer_empty_speech_handled_without_calling_llm() -> None:
    # Provider that would error if called
    provider = MockLLMProvider(is_online=False)
    engine = LectureUnderstandingEngine(provider=provider)

    visual = [{"timestamp": 5.0, "source": "camera", "type": "keyframe", "frame_path": "/tmp/board.jpg"}]
    understanding = engine.analyze_block(0.0, 10.0, [], visual)

    assert understanding.topic == "Silent Interval / Visual Demonstration"
    assert len(understanding.concepts) == 0
    assert len(understanding.visual_references) == 1
    assert understanding.visual_references[0].frame_path == "/tmp/board.jpg"
    assert understanding.raw_transcript_ref == ""


def test_analyzer_llm_unavailable_graceful_fallback() -> None:
    provider = MockLLMProvider(is_online=False)
    engine = LectureUnderstandingEngine(provider=provider)

    speech = [{"start": 1.0, "end": 4.0, "text": "Speech while model is down"}]
    understanding = engine.analyze_block(1.0, 4.0, speech, [])

    # Does NOT raise exception or crash; returns safe fallback
    assert understanding.confidence == 0.0
    assert "Unavailable" in understanding.topic
    assert understanding.raw_transcript_ref == "Speech while model is down"


def test_analyzer_malformed_llm_response_graceful_fallback() -> None:
    # LLM returns malformed garbage instead of JSON
    provider = MockLLMProvider(response_generator=lambda p: "Not valid json at all")
    engine = LectureUnderstandingEngine(provider=provider)

    speech = [{"start": 1.0, "end": 4.0, "text": "Some lecture segment"}]
    understanding = engine.analyze_block(1.0, 4.0, speech, [])

    assert understanding.confidence == 0.0
    assert "Parse Error" in understanding.topic
    assert understanding.raw_transcript_ref == "Some lecture segment"
