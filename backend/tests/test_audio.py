"""Unit tests for audio loading, normalization, and WAV operations."""

import numpy as np
import pytest
from speech_engine.audio import (
    AudioInput,
    STANDARD_SAMPLE_RATE,
    load_audio,
    normalize_audio,
    resample_linear,
    save_wav,
)


def test_normalize_audio_peak() -> None:
    # Create array with max peak 0.5
    raw = np.array([-0.5, 0.2, 0.5, -0.1], dtype=np.float32)
    norm = normalize_audio(raw, target_peak=0.95)

    assert np.isclose(np.max(np.abs(norm)), 0.95, atol=1e-5)
    assert norm.dtype == np.float32


def test_normalize_audio_empty() -> None:
    empty = np.array([], dtype=np.float32)
    res = normalize_audio(empty)
    assert len(res) == 0


def test_normalize_audio_near_zero() -> None:
    zeros = np.zeros(100, dtype=np.float32)
    res = normalize_audio(zeros)
    assert np.all(res == 0.0)


def test_resample_linear() -> None:
    # 1 second of 8000 Hz resampled to 16000 Hz
    t = np.linspace(0, 1.0, 8000, endpoint=False)
    orig = np.sin(2 * np.pi * 440 * t).astype(np.float32)

    resampled = resample_linear(orig, orig_sr=8000, target_sr=16000)
    assert len(resampled) == 16000


def test_save_and_load_wav(tmp_path) -> None:
    sr = 16000
    duration = 0.5  # 500 ms
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    samples = (0.7 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)

    file_path = tmp_path / "test_tone.wav"
    saved_path = save_wav(file_path, samples, sample_rate=sr)
    assert saved_path.is_file()

    loaded = load_audio(saved_path, target_sr=sr)
    assert isinstance(loaded, AudioInput)
    assert loaded.sample_rate == sr
    assert np.isclose(loaded.duration, duration, atol=0.01)
    assert len(loaded.samples) == len(samples)


def test_load_audio_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        load_audio("non_existent_path_12345.wav")
