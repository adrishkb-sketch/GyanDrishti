"""Demonstration of GyanDrishti Milestone 4: Local Lecture Understanding Engine."""

import json
import time
from pathlib import Path
import sys

backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from understanding_engine import (
    LectureUnderstandingEngine,
    MockLLMProvider,
    OllamaProvider,
)
from temporal_engine.timeline import create_lecture_timeline

# 1. Check if a local LLM runtime (e.g. Ollama) is active
ollama = OllamaProvider(model="llama3.2")
if ollama.is_available():
    print(">> Detected active local Ollama runtime! Using OllamaProvider.")
    provider = ollama
else:
    print(">> No active local Ollama daemon detected at http://localhost:11434.")
    print(">> Using deterministic local MockLLMProvider for offline demonstration.\n")
    provider = MockLLMProvider(
        response_generator=lambda prompt: """{
            "topic": "Student Introduction and Academic Context",
            "concepts": [
                {
                    "name": "Academic Standing and Technical Background",
                    "explanation": "Student introduces self as Adrish Mukherjee, currently studying in the second year of Information Technology (IT).",
                    "timestamp_start": 2.0,
                    "timestamp_end": 10.0
                },
                {
                    "name": "Personal Interests",
                    "explanation": "Student expresses interest in playing sports/games ('khelte bhalobashi').",
                    "timestamp_start": 10.0,
                    "timestamp_end": 13.5
                }
            ],
            "definitions": [],
            "equations": [],
            "important_points": [
                {
                    "point": "Speaker is an IT 2nd-year student with extracurricular athletic interests.",
                    "timestamp_start": 2.0,
                    "timestamp_end": 13.5,
                    "importance": "high"
                }
            ],
            "visual_references": [
                {
                    "timestamp": 2.88,
                    "source": "camera",
                    "event_type": "keyframe",
                    "frame_path": "backend/video_engine/output_frames/camera_f16_1791296502111.jpg",
                    "relevance": "Keyframe showing speaker during introductory remarks."
                }
            ],
            "question_candidates": [
                {
                    "question": "Which academic year and department is the student currently enrolled in?",
                    "expected_answer": "Second year of Information Technology (IT).",
                    "difficulty": "easy",
                    "relevant_timestamp": 7.0
                }
            ],
            "confidence": 0.98
        }"""
    )

engine = LectureUnderstandingEngine(provider=provider)

# 2. Load real fused timeline from Milestone 1 speech and Milestone 2 video
speech_json = backend_root / "recordings" / "validation_test.json"
manifest_candidates = sorted(list(backend_root.glob("**/manifests/lecture_*.json")), reverse=True)
video_manifest = None
for p in manifest_candidates:
    with open(p, "r", encoding="utf-8") as f:
        if len(json.load(f).get("events", [])) > 0:
            video_manifest = p
            break

print("=" * 80)
print("  GyanDrishti Milestone 4: Local Lecture Understanding Demo")
print("=" * 80)
print(f"Speech Input:  {speech_json}")
print(f"Video Input:   {video_manifest}")
print(f"LLM Provider:  {provider.get_model_name()}\n")

# Build temporal timeline
timeline = create_lecture_timeline(
    speech_source=speech_json,
    visual_source=video_manifest,
    lecture_id="demo_lecture_001",
)

# Extract understanding across all synchronized multimodal blocks
t0 = time.perf_counter()
understandings = engine.analyze_timeline(timeline)
t_elapsed = time.perf_counter() - t0

print(f"Analysis Completed in {t_elapsed:.4f}s ({len(understandings)} block(s) analyzed)\n")

for idx, u in enumerate(understandings, start=1):
    print(f"=== UNDERSTANDING BLOCK #{idx} [{u.time_start:.2f}s -> {u.time_end:.2f}s] ===")
    print(f"Topic:        {u.topic} (Confidence: {u.confidence})")
    print(f"Raw Source:   \"{u.raw_transcript_ref}\"")
    print(f"Concepts ({len(u.concepts)}):")
    for c in u.concepts:
        print(f"  - [{c.timestamp_start:.2f}s-{c.timestamp_end:.2f}s] {c.name}: {c.explanation}")
    print(f"Key Points ({len(u.important_points)}):")
    for p in u.important_points:
        print(f"  - {p.point} (Priority: {p.importance})")
    print(f"Visual Evidence ({len(u.visual_references)}):")
    for v in u.visual_references:
        print(f"  - [{v.timestamp:.2f}s] [{v.source}] {v.relevance} -> {v.frame_path}")
    print(f"Revision Questions ({len(u.question_candidates)}):")
    for q in u.question_candidates:
        print(f"  - {q.question} (Ans: {q.expected_answer})")
    print()

print("=" * 80)
