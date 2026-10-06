"""Unit and integration tests for ASR engine."""

from typing import List, Optional, Tuple
from unittest.mock import MagicMock, patch
import numpy as np
import pytest

from speech_engine.asr import BaseASRModel, FasterWhisperASR
from speech_engine.schemas import TranscriptionSegment
from speech_engine.transcription import transcribe_chunk, transcribe_file
from speech_engine.cli import build_parser


class MockASREngine(BaseASRModel):
    """Mock ASR model for fast unit testing without downloading model weights."""

    def __init__(self, segments=None, detected_lang="en"):
        self.segments = segments or [
            TranscriptionSegment(
                id=1,
                start=0.0,
                end=2.5,
                text="Hello class, welcome to physics.",
                language=["en"],
                confidence=None,
            ),
            TranscriptionSegment(
                id=2,
                start=2.6,
                end=5.0,
                text="আজকে আমরা magnetic field নিয়ে আলোচনা করব।",
                language=["bn", "en"],
                confidence=None,
            ),
        ]
        self.detected_lang = detected_lang
        self.device = "cpu"
        self.compute_type = "int8"

    def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        language: Optional[str] = None,
        vad_filter: bool = True,
    ) -> Tuple[List[TranscriptionSegment], Optional[str]]:
        return self.segments, self.detected_lang


def test_transcribe_chunk_with_mock() -> None:
    engine = MockASREngine()
    sr = 16000
    dummy_audio = np.zeros(sr * 5, dtype=np.float32)

    result = transcribe_chunk(
        audio=dummy_audio,
        sample_rate=sr,
        asr_engine=engine,
        model_name="small",
        lecture_id="lec-test-1",
    )

    assert result.lecture_id == "lec-test-1"
    assert result.duration == 5.0
    assert result.processing_time > 0.0
    assert result.real_time_factor >= 0.0
    assert len(result.segments) == 2
    # Verify Bengali & English code-switching was identified
    assert "bn" in result.language_summary
    assert "en" in result.language_summary
    # Ensure confidence is None (no fabricated values)
    assert result.segments[0].confidence is None


def test_offline_only_error_when_model_missing(tmp_path) -> None:
    """Verifies that offline_only mode raises an error if weights are not downloaded."""
    with pytest.raises(RuntimeError, match="Offline-only mode enabled"):
        FasterWhisperASR(
            model_name="nonexistent_model",
            models_dir=tmp_path,
            offline_only=True,
        )


def test_cli_argument_parser() -> None:
    parser = build_parser()

    # Test record sub-command defaults
    args_rec = parser.parse_args(["record", "--duration", "15", "--model", "base"])
    assert args_rec.command == "record"
    assert args_rec.duration == 15.0
    assert args_rec.model == "base"

    # Test transcribe sub-command
    args_ts = parser.parse_args(["transcribe", "test.wav", "--offline"])
    assert args_ts.command == "transcribe"
    assert args_ts.audio_file == "test.wav"
    assert args_ts.offline is True
