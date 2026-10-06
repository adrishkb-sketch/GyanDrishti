"""ASR (Automatic Speech Recognition) engine wrapper for GyanDrishti.

Provides offline-first multilingual transcription optimized for Apple Silicon
and low-memory classroom environments.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generator, List, Optional, Tuple, Union

import numpy as np

from speech_engine.models import (
    DEFAULT_MODEL_NAME,
    get_model_dir,
    get_optimal_compute_type,
    is_model_downloaded,
)
from speech_engine.schemas import TranscriptionSegment
from speech_engine.vad import get_vad_parameters_dict

logger = logging.getLogger(__name__)


class BaseASRModel(ABC):
    """Abstract interface for speech-to-text models in GyanDrishti."""

    @abstractmethod
    def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        language: Optional[str] = None,
        vad_filter: bool = True,
    ) -> Tuple[List[TranscriptionSegment], Optional[str]]:
        """Transcribes audio array into timestamped segments and detected audio language.

        Returns:
            Tuple of (list_of_segments, detected_language_code)
        """
        pass


class FasterWhisperASR(BaseASRModel):
    """Offline Multilingual ASR using faster-whisper (CTranslate2).

    Optimized for Apple Silicon M2 with INT8 quantization to achieve low latency
    and minimal memory footprint (< 1 GB RAM for 'small' model).
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        models_dir: Optional[Path] = None,
        device: str = "cpu",
        compute_type: Optional[str] = None,
        cpu_threads: int = 4,
        offline_only: bool = False,
    ) -> None:
        """Args:

        model_name: Name or size of Whisper model (e.g. 'small', 'base').
        models_dir: Root directory for local model storage.
        device: 'cpu' or 'cuda' (use 'cpu' on Apple Silicon macOS).
        compute_type: Quantization precision ('int8', 'float16', 'float32'). Defaults to 'int8'.
        cpu_threads: Number of CPU worker threads for inference.
        offline_only: If True, strictly requires pre-downloaded local weights; never accesses internet.
        """
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type or get_optimal_compute_type()
        self.cpu_threads = cpu_threads
        self.offline_only = offline_only

        model_path = get_model_dir(model_name, models_dir)
        has_local = is_model_downloaded(model_name, models_dir)

        if offline_only and not has_local:
            raise RuntimeError(
                f"Offline-only mode enabled, but model '{model_name}' was not found at {model_path}. "
                f"Please run 'python -m speech_engine download --model {model_name}' while online first."
            )

        # Import faster_whisper lazily to keep unit tests fast
        from faster_whisper import WhisperModel

        if has_local:
            logger.info(
                "Loading offline model '%s' from local directory: %s (compute_type=%s)",
                model_name, model_path, self.compute_type
            )
            load_target = str(model_path)
            local_files_only = True
        else:
            logger.info(
                "Local model '%s' not found. Loading/downloading via faster-whisper cache...",
                model_name
            )
            load_target = model_name
            local_files_only = False

        self._model = WhisperModel(
            model_size_or_path=load_target,
            device=self.device,
            compute_type=self.compute_type,
            cpu_threads=self.cpu_threads,
            local_files_only=local_files_only,
        )

    def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        language: Optional[str] = None,
        vad_filter: bool = True,
    ) -> Tuple[List[TranscriptionSegment], Optional[str]]:
        """Transcribes audio array into timestamped segments.

        IMPORTANT:
        - Uses task="transcribe" to preserve original spoken language (never "translate").
        - Emits confidence: null (no fabricated confidence scores).
        """
        if len(audio) == 0:
            return [], None

        vad_params = get_vad_parameters_dict() if vad_filter else None

        # faster-whisper transcribe takes audio as 1D float32 array
        segments_gen, info = self._model.transcribe(
            audio=audio,
            language=language,
            task="transcribe",  # Strictly preserve original spoken language
            beam_size=5,
            vad_filter=vad_filter,
            vad_parameters=vad_params,
            temperature=0.0,
            compression_ratio_threshold=2.4,
            log_prob_threshold=-1.0,
            no_speech_threshold=0.6,
        )

        detected_language = info.language if info else None

        segments: List[TranscriptionSegment] = []
        for idx, seg in enumerate(segments_gen, start=1):
            text = seg.text.strip()
            if not text:
                continue

            segments.append(
                TranscriptionSegment(
                    id=idx,
                    start=round(float(seg.start), 2),
                    end=round(float(seg.end), 2),
                    text=text,
                    language=[detected_language] if detected_language else [],
                    confidence=None,  # No fabricated confidence scores
                )
            )

        return segments, detected_language
