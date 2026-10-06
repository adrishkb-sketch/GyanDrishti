"""GyanDrishti Speech Engine - Offline Multilingual ASR.

Core foundation module for classroom speech intelligence across English,
Hindi, Bengali, and code-switched lectures.
"""

from speech_engine.asr import BaseASRModel, FasterWhisperASR
from speech_engine.audio import (
    AudioInput,
    STANDARD_SAMPLE_RATE,
    calculate_audio_metrics,
    get_default_input_device,
    get_device_info,
    list_microphones,
    load_audio,
    normalize_audio,
    record_microphone,
    record_raw_audio,
    save_wav,
)
from speech_engine.language import aggregate_languages, detect_segment_languages
from speech_engine.models import (
    AVAILABLE_MODELS,
    DEFAULT_MODEL_NAME,
    ModelMetadata,
    download_model,
    is_model_downloaded,
)
from speech_engine.schemas import TranscriptionResult, TranscriptionSegment
from speech_engine.transcription import (
    transcribe_chunk,
    transcribe_file,
    transcribe_microphone,
)
from speech_engine.vad import SpeechInterval, VoiceActivityDetector

__version__ = "0.1.0"

__all__ = [
    "AudioInput",
    "BaseASRModel",
    "FasterWhisperASR",
    "ModelMetadata",
    "SpeechInterval",
    "TranscriptionResult",
    "TranscriptionSegment",
    "VoiceActivityDetector",
    "AVAILABLE_MODELS",
    "DEFAULT_MODEL_NAME",
    "STANDARD_SAMPLE_RATE",
    "aggregate_languages",
    "detect_segment_languages",
    "download_model",
    "is_model_downloaded",
    "list_microphones",
    "load_audio",
    "normalize_audio",
    "record_microphone",
    "save_wav",
    "transcribe_chunk",
    "transcribe_file",
    "transcribe_microphone",
]
