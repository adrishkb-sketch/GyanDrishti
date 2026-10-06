"""Unit tests for prompt formatting module."""

import pytest
from understanding_engine.prompts import (
    SYSTEM_UNDERSTANDING_PROMPT,
    format_synchronized_block_prompt,
)


def test_system_prompt_includes_multilingual_rules() -> None:
    assert "BANGLISH" in SYSTEM_UNDERSTANDING_PROMPT
    assert "SPOKEN INFORMATION VS VISUAL EVIDENCE" in SYSTEM_UNDERSTANDING_PROMPT
    assert "EQUATIONS" in SYSTEM_UNDERSTANDING_PROMPT
    assert "OUTPUT SCHEMA" in SYSTEM_UNDERSTANDING_PROMPT


def test_format_synchronized_block_prompt_speech_and_visual() -> None:
    speech = [
        {"start": 10.0, "end": 14.5, "text": "Ekhane amra current dekhchi", "language": ["bn", "en"]}
    ]
    visual = [
        {"timestamp": 12.0, "source": "camera", "type": "keyframe", "frame_path": "/tmp/f1.jpg", "change_score": 0.45}
    ]

    prompt = format_synchronized_block_prompt(
        start_time=10.0,
        end_time=15.0,
        speech_segments=speech,
        visual_events=visual,
        lecture_id="test_lec",
    )

    assert "10.00s -> 15.00s" in prompt
    assert "SESSION ID: test_lec" in prompt
    assert "Ekhane amra current dekhchi" in prompt
    assert "camera" in prompt
    assert "/tmp/f1.jpg" in prompt


def test_format_synchronized_block_prompt_empty_inputs() -> None:
    prompt = format_synchronized_block_prompt(
        start_time=0.0,
        end_time=5.0,
        speech_segments=[],
        visual_events=[],
    )
    assert "No active speech detected" in prompt
    assert "No visual keyframes" in prompt
