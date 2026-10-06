"""High-level transcription API for GyanDrishti Speech Engine.

Coordinates audio ingestion, VAD, ASR inference, multi-language detection,
and metrics computation into structured, immutable source transcripts.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import List, Optional, Union

import numpy as np

from speech_engine.asr import BaseASRModel, FasterWhisperASR
from speech_engine.audio import (
    AudioInput,
    STANDARD_SAMPLE_RATE,
    load_audio,
    normalize_audio,
    record_microphone,
    save_wav,
)
from speech_engine.language import aggregate_languages, detect_segment_languages
from speech_engine.models import DEFAULT_MODEL_NAME
from speech_engine.schemas import TranscriptionResult, TranscriptionSegment

logger = logging.getLogger(__name__)


def _postprocess_segments(
    raw_segments: List[TranscriptionSegment],
    model_language: Optional[str],
) -> List[TranscriptionSegment]:
    """Applies multilingual script detection and code-switching analysis to each segment."""
    processed: List[TranscriptionSegment] = []
    for seg in raw_segments:
        # Detect languages combining script, lexical cues, and model signal
        segment_langs = detect_segment_languages(
            text=seg.text,
            model_language=model_language,
        )
        processed.append(
            TranscriptionSegment(
                id=seg.id,
                start=seg.start,
                end=seg.end,
                text=seg.text,
                language=segment_langs,
                confidence=None,  # Preserves honesty: strictly null
                words=seg.words,
            )
        )
    return processed


def transcribe_chunk(
    audio: np.ndarray,
    sample_rate: int = STANDARD_SAMPLE_RATE,
    asr_engine: Optional[BaseASRModel] = None,
    model_name: str = DEFAULT_MODEL_NAME,
    language: Optional[str] = None,
    vad: bool = True,
    lecture_id: Optional[str] = None,
    offline_only: bool = False,
) -> TranscriptionResult:
    """Transcribes an in-memory audio chunk.

    Args:
        audio: 1D numpy array of float32 samples.
        sample_rate: Sample rate in Hz (default 16000).
        asr_engine: Pre-instantiated ASR engine instance (optional).
        model_name: Model size/name if creating new engine (default 'small').
        language: Language code to force (e.g. 'en', 'hi', 'bn') or None for auto.
        vad: Whether to apply VAD silence filtering.
        lecture_id: Optional identifier for lecture/session.
        offline_only: If True, requires local model weights without internet.

    Returns:
        TranscriptionResult object.
    """
    if len(audio) == 0:
        return TranscriptionResult(
            lecture_id=lecture_id,
            duration=0.0,
            processing_time=0.0,
            real_time_factor=0.0,
            model_name=model_name,
            device="cpu",
            compute_type="int8",
            language_summary=[],
            segments=[],
            raw_text="",
        )

    duration = float(len(audio)) / float(sample_rate)

    engine = asr_engine or FasterWhisperASR(
        model_name=model_name,
        offline_only=offline_only,
    )

    t0 = time.perf_counter()
    raw_segments, detected_model_lang = engine.transcribe(
        audio=audio,
        sample_rate=sample_rate,
        language=language,
        vad_filter=vad,
    )
    t1 = time.perf_counter()

    proc_time = max(0.001, t1 - t0)
    rtf = proc_time / duration if duration > 0 else 0.0

    segments = _postprocess_segments(raw_segments, detected_model_lang)
    lang_summary = aggregate_languages(segments)
    raw_text = " ".join(s.text for s in segments).strip()

    device = getattr(engine, "device", "cpu")
    compute_type = getattr(engine, "compute_type", "int8")

    return TranscriptionResult(
        lecture_id=lecture_id,
        duration=duration,
        processing_time=proc_time,
        real_time_factor=rtf,
        model_name=model_name,
        device=device,
        compute_type=compute_type,
        language_summary=lang_summary,
        segments=segments,
        raw_text=raw_text,
    )


def transcribe_file(
    file_path: Union[str, Path],
    model_name: str = DEFAULT_MODEL_NAME,
    language: Optional[str] = None,
    vad: bool = True,
    lecture_id: Optional[str] = None,
    models_dir: Optional[Path] = None,
    offline_only: bool = False,
    asr_engine: Optional[BaseASRModel] = None,
) -> TranscriptionResult:
    """Transcribes an audio file from disk (WAV, MP3, M4A).

    Args:
        file_path: Path to the target audio file.
        model_name: Model size/name (default 'small').
        language: Language code to force (or None for auto-detect).
        vad: Whether to apply VAD silence filtering.
        lecture_id: Optional lecture session ID.
        models_dir: Custom directory for model weights.
        offline_only: Require weights locally without internet.
        asr_engine: Pre-warmed ASR engine.

    Returns:
        TranscriptionResult object.
    """
    path = Path(file_path).resolve()
    audio_input = load_audio(path)

    engine = asr_engine or FasterWhisperASR(
        model_name=model_name,
        models_dir=models_dir,
        offline_only=offline_only,
    )

    result = transcribe_chunk(
        audio=audio_input.samples,
        sample_rate=audio_input.sample_rate,
        asr_engine=engine,
        model_name=model_name,
        language=language,
        vad=vad,
        lecture_id=lecture_id,
        offline_only=offline_only,
    )
    result.audio_path = str(path)
    return result


def transcribe_microphone(
    duration: float = 30.0,
    output_audio_path: Optional[Union[str, Path]] = None,
    output_json_path: Optional[Union[str, Path]] = None,
    model_name: str = DEFAULT_MODEL_NAME,
    language: Optional[str] = None,
    vad: bool = True,
    lecture_id: Optional[str] = None,
    device_id: Optional[int] = None,
    offline_only: bool = False,
    asr_engine: Optional[BaseASRModel] = None,
) -> TranscriptionResult:
    """Records audio from the microphone and runs local transcription.

    Args:
        duration: Recording duration in seconds (default: 30.0s).
        output_audio_path: Optional path to save the recorded WAV file.
        output_json_path: Optional path to save the structured JSON transcript.
        model_name: ASR model to use (default: 'small').
        language: Language code or None for auto.
        vad: Whether to apply VAD silence filtering.
        lecture_id: Optional lecture ID.
        device_id: Specific microphone input device ID.
        offline_only: Require local model weights.
        asr_engine: Pre-warmed engine.

    Returns:
        TranscriptionResult object.
    """
    logger.info("Recording %.1f seconds from microphone...", duration)
    audio_input = record_microphone(
        duration=duration,
        sample_rate=STANDARD_SAMPLE_RATE,
        device_id=device_id,
    )

    # Save audio recording locally if requested or by default to recordings/
    if output_audio_path:
        save_path = Path(output_audio_path)
    else:
        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        recordings_dir = Path(__file__).resolve().parent.parent / "recordings"
        save_path = recordings_dir / f"mic_{timestamp_str}.wav"

    save_wav(save_path, audio_input.samples, audio_input.sample_rate)
    logger.info("Audio recording saved locally to: %s", save_path)

    result = transcribe_chunk(
        audio=audio_input.samples,
        sample_rate=audio_input.sample_rate,
        asr_engine=asr_engine,
        model_name=model_name,
        language=language,
        vad=vad,
        lecture_id=lecture_id,
        offline_only=offline_only,
    )
    result.audio_path = str(save_path)

    if output_json_path:
        result.save_json(output_json_path)
        logger.info("Transcript JSON saved to: %s", output_json_path)

    return result
