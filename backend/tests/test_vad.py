"""Unit tests for Voice Activity Detection and interval handling."""

import numpy as np
from speech_engine.vad import (
    SpeechInterval,
    VoiceActivityDetector,
    get_vad_parameters_dict,
)


def test_vad_synthetic_silence() -> None:
    # 2 seconds of pure silence / low noise
    sr = 16000
    silence = np.random.normal(0, 0.0001, sr * 2).astype(np.float32)

    vad = VoiceActivityDetector(energy_threshold=0.02)
    intervals = vad.detect_intervals(silence, sample_rate=sr)

    # Should not crash and should return safe fallback interval
    assert len(intervals) >= 1
    assert intervals[0].start == 0.0


def test_vad_speech_burst_detection() -> None:
    sr = 16000
    # 1 second silence, 1.5 seconds speech tone, 1 second silence
    t_silence = np.zeros(int(1.0 * sr), dtype=np.float32)
    t_speech_time = np.linspace(0, 1.5, int(1.5 * sr), endpoint=False)
    speech = (0.5 * np.sin(2 * np.pi * 300 * t_speech_time)).astype(np.float32)

    audio = np.concatenate([t_silence, speech, t_silence])
    assert len(audio) == int(3.5 * sr)

    vad = VoiceActivityDetector(
        frame_ms=30,
        energy_threshold=0.02,
        min_speech_ms=200,
        min_silence_ms=400,
        speech_pad_ms=200,
    )
    intervals = vad.detect_intervals(audio, sample_rate=sr)

    assert len(intervals) == 1
    interval = intervals[0]
    # Tone starts at 1.0s and ends at 2.5s. With padding, should span roughly 0.8s to 2.7s
    assert interval.start <= 1.05
    assert interval.end >= 2.45


def test_vad_parameters_dict() -> None:
    params = get_vad_parameters_dict()
    assert "threshold" in params
    assert "speech_pad_ms" in params
    assert "min_silence_duration_ms" in params
    assert params["speech_pad_ms"] == 400
