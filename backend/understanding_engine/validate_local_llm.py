"""Multilingual & Grounding Validation Suite for GyanDrishti Understanding Engine.

Evaluates local LLM performance across 5 pedagogical benchmark cases:
1. English classroom speech
2. Hindi + English (Hinglish)
3. Banglish + English
4. Noisy ASR with uncertain proper noun (Real GyanDrishti recording)
5. Technical explanation containing an explicitly stated equation
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional

from understanding_engine.analyzer import LectureUnderstandingEngine
from understanding_engine.llm import (
    BaseLLMProvider,
    MockLLMProvider,
    OllamaProvider,
)
from understanding_engine.schemas import LectureUnderstanding

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("validation_suite")


BENCHMARK_CASES = [
    {
        "id": "ex1_english",
        "name": "Example 1: English Classroom Speech",
        "language_type": "English",
        "start_time": 0.0,
        "end_time": 18.0,
        "speech": [
            {
                "start": 0.5,
                "end": 8.0,
                "text": "Today we will study Faraday's Law of Electromagnetic Induction.",
                "language": ["en"],
            },
            {
                "start": 8.5,
                "end": 17.5,
                "text": "Whenever the magnetic flux linking an electrical circuit changes, an electromotive force is induced in the circuit.",
                "language": ["en"],
            },
        ],
        "visual_events": [
            {
                "timestamp": 6.2,
                "source": "camera",
                "type": "keyframe",
                "frame_path": "recordings/frames/frame_001.jpg",
                "change_score": 0.38,
            }
        ],
        "expected_equation": False,
        "uncertain_noun": False,
    },
    {
        "id": "ex2_hindi_english",
        "name": "Example 2: Hindi + English (Hinglish)",
        "language_type": "Hindi + English",
        "start_time": 20.0,
        "end_time": 36.0,
        "speech": [
            {
                "start": 20.5,
                "end": 28.0,
                "text": "Ab hum dekhenge ki magnetic flux ka change kaise EMF induce karta hai.",
                "language": ["hi", "en"],
            },
            {
                "start": 28.5,
                "end": 35.5,
                "text": "Agar coil me turns increase karte hain, toh induced voltage proportionally increase ho jata hai.",
                "language": ["hi", "en"],
            },
        ],
        "visual_events": [
            {
                "timestamp": 27.0,
                "source": "camera",
                "type": "keyframe",
                "frame_path": "recordings/frames/frame_002.jpg",
                "change_score": 0.42,
            }
        ],
        "expected_equation": False,
        "uncertain_noun": False,
    },
    {
        "id": "ex3_banglish_english",
        "name": "Example 3: Banglish + English",
        "language_type": "Banglish + English",
        "start_time": 40.0,
        "end_time": 55.0,
        "speech": [
            {
                "start": 40.5,
                "end": 47.0,
                "text": "Ekhane amra basically dekhchi je current ta increase korche because circuit e resistance komche.",
                "language": ["bn", "en"],
            },
            {
                "start": 47.5,
                "end": 54.5,
                "text": "Jodi voltage constant thake, tahole resistance komle current oboshshoi barbe.",
                "language": ["bn", "en"],
            },
        ],
        "visual_events": [
            {
                "timestamp": 45.0,
                "source": "screen",
                "type": "keyframe",
                "frame_path": "recordings/frames/frame_003.jpg",
                "change_score": 0.29,
            }
        ],
        "expected_equation": False,
        "uncertain_noun": False,
    },
    {
        "id": "ex4_noisy_asr_proper_noun",
        "name": "Example 4: Noisy ASR with Uncertain Proper Noun (Real Recording)",
        "language_type": "Bengali / Banglish (Noisy ASR)",
        "start_time": 2.0,
        "end_time": 13.51,
        "speech": [
            {
                "start": 2.0,
                "end": 13.51,
                "text": "HALLO HALLO, AAMAN NAM AUDRISHMAR GANAR JEE, AAMI IT SECOND YEAR E PARASUNA KORI, AAMI KHELTE BHALO BASHI.",
                "language": ["bn", "en"],
            }
        ],
        "visual_events": [
            {
                "timestamp": 5.0,
                "source": "camera",
                "type": "keyframe",
                "frame_path": "recordings/frames/frame_speaker.jpg",
                "change_score": 0.51,
            }
        ],
        "expected_equation": False,
        "uncertain_noun": True,
    },
    {
        "id": "ex5_technical_equation",
        "name": "Example 5: Technical Explanation with Explicit Equation",
        "language_type": "English (Explicit Formula)",
        "start_time": 60.0,
        "end_time": 75.0,
        "speech": [
            {
                "start": 60.5,
                "end": 67.0,
                "text": "According to Ohm's law, the electric current is directly proportional to voltage and inversely proportional to resistance.",
                "language": ["en"],
            },
            {
                "start": 67.5,
                "end": 74.5,
                "text": "Mathematically, the relationship is stated as: I equals V divided by R.",
                "language": ["en"],
            },
        ],
        "visual_events": [
            {
                "timestamp": 68.0,
                "source": "camera",
                "type": "keyframe",
                "frame_path": "recordings/frames/frame_004.jpg",
                "change_score": 0.65,
            }
        ],
        "expected_equation": True,
        "uncertain_noun": False,
    },
]


def run_single_test(engine: LectureUnderstandingEngine, test_case: Dict[str, Any]) -> Dict[str, Any]:
    """Runs a single benchmark inference and validates quality."""
    start_wall = time.perf_counter()
    try:
        understanding = engine.analyze_block(
            start_time=test_case["start_time"],
            end_time=test_case["end_time"],
            speech_segments=test_case["speech"],
            visual_events=test_case["visual_events"],
            lecture_id="benchmark_suite",
        )
        elapsed_sec = time.perf_counter() - start_wall
        valid_json = True
        pydantic_valid = isinstance(understanding, LectureUnderstanding)
    except Exception as e:
        elapsed_sec = time.perf_counter() - start_wall
        logger.error("Error executing benchmark %s: %s", test_case["id"], e)
        return {
            "test_id": test_case["id"],
            "test_name": test_case["name"],
            "elapsed_sec": round(elapsed_sec, 2),
            "valid_json": False,
            "pydantic_valid": False,
            "semantic_quality": f"Failed: {e}",
            "hallucination_risk": "N/A",
            "understanding": None,
        }

    # Evaluate hallucinations and grounding
    hallucination_risks = []
    semantic_notes = []

    # Check proper noun safety in Example 4
    if test_case["uncertain_noun"]:
        serialized = understanding.to_json().lower()
        if "adrish mukherjee" in serialized or "adrishmar ganer" in serialized:
            hallucination_risks.append("CRITICAL: Hallucinated specific proper noun from noisy ASR phonetics!")
        else:
            semantic_notes.append("Proper noun safely treated as uncertain or preserved cautiously.")

    # Check equation grounding
    if not test_case["expected_equation"]:
        if understanding.equations:
            hallucination_risks.append("CRITICAL: Extracted equation when none was dictated in speech!")
        else:
            semantic_notes.append("Correctly extracted zero equations (no hallucination from visual frames).")
    else:
        if understanding.equations:
            semantic_notes.append(f"Correctly extracted explicitly spoken equation: {understanding.equations[0].latex_or_text}")
        else:
            semantic_notes.append("Missed explicitly dictated equation.")

    # Check concepts
    if understanding.concepts:
        semantic_notes.append(f"Identified {len(understanding.concepts)} concepts (Primary: '{understanding.concepts[0].name}')")
    else:
        semantic_notes.append("No concepts extracted.")

    hallucination_risk = "; ".join(hallucination_risks) if hallucination_risks else "Low (Strictly grounded in source)"
    semantic_quality = "; ".join(semantic_notes)

    return {
        "test_id": test_case["id"],
        "test_name": test_case["name"],
        "elapsed_sec": round(elapsed_sec, 2),
        "valid_json": valid_json,
        "pydantic_valid": pydantic_valid,
        "semantic_quality": semantic_quality,
        "hallucination_risk": hallucination_risk,
        "understanding": understanding,
    }


def run_benchmark_suite(provider: BaseLLMProvider) -> List[Dict[str, Any]]:
    """Runs all 5 benchmark cases against the given provider."""
    engine = LectureUnderstandingEngine(provider=provider)
    results = []
    for tc in BENCHMARK_CASES:
        logger.info("Executing benchmark: %s ...", tc["name"])
        res = run_single_test(engine, tc)
        results.append(res)
    return results


def main() -> None:
    provider = OllamaProvider(model="llama3.2:3b")
    print(f"Connecting to provider: {provider.get_model_name()}...")
    if not provider.is_available():
        print("ERROR: Ollama provider is not available.")
        return

    print("Running 5 multilingual benchmark tests on real local LLM...")
    results = run_benchmark_suite(provider)

    print("\n" + "=" * 90)
    print("GYANDRISHTI UNDERSTANDING ENGINE — LOCAL LLM VALIDATION REPORT")
    print("=" * 90)
    header = f"{'Test Case':<38} | {'Latency':<8} | {'JSON':<6} | {'Pydantic':<8} | {'Hallucination Risk'}"
    print(header)
    print("-" * 90)
    for r in results:
        t_name = r["test_name"][:36]
        lat = f"{r['elapsed_sec']}s"
        v_json = "PASS" if r["valid_json"] else "FAIL"
        v_pyd = "PASS" if r["pydantic_valid"] else "FAIL"
        h_risk = r["hallucination_risk"][:30]
        print(f"{t_name:<38} | {lat:<8} | {v_json:<6} | {v_pyd:<8} | {h_risk}")

    print("\n" + "=" * 90)
    print("DETAILED PEDAGOGICAL EXTRACTIONS")
    print("=" * 90)
    for r in results:
        print(f"\n>>> [{r['test_id']}] {r['test_name']}")
        print(f"    Semantic Notes: {r['semantic_quality']}")
        u = r["understanding"]
        if u:
            print(f"    Topic: \"{u.topic}\"")
            print(f"    Concepts: {[c.name for c in u.concepts]}")
            print(f"    Definitions: {[d.term + ': ' + d.definition for d in u.definitions]}")
            print(f"    Equations: {[eq.latex_or_text for eq in u.equations]}")
            print(f"    Key Points: {[p.point for p in u.important_points]}")
            print(f"    Visual References: {[v.relevance for v in u.visual_references]}")
            print(f"    Confidence: {u.confidence}")


if __name__ == "__main__":
    main()
