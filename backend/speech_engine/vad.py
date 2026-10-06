"""Voice Activity Detection (VAD) module for GyanDrishti.

Filters long classroom silences, detects speech intervals, preserves timing
integrity, and ensures speech boundaries (plosives, consonants) are not
clipped or truncated.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SpeechInterval:
    """Represents an active speech interval with exact timestamps."""

    start: float  # seconds
    end: float    # seconds

    @property
    def duration(self) -> float:
        return self.end - self.start


class VoiceActivityDetector:
    """Energy-based and statistical Voice Activity Detector with protective speech hangover padding.

    Designed for lightweight, zero-dependency speech segmentation and silence
    rejection to complement Silero VAD in the ASR pipeline.
    """

    def __init__(
        self,
        frame_ms: int = 30,
        energy_threshold: float = 0.015,
        min_speech_ms: int = 250,
        min_silence_ms: int = 500,
        speech_pad_ms: int = 350,
    ) -> None:
        """Args:

        frame_ms: Analysis frame size in milliseconds (default: 30ms).
        energy_threshold: Relative RMS energy threshold for speech trigger.
        min_speech_ms: Minimum active speech duration to prevent trigger on brief pops/clicks.
        min_silence_ms: Minimum silence duration to treat as speech boundary.
        speech_pad_ms: Margin added before and after speech to protect consonants and vowels.
        """
        self.frame_ms = frame_ms
        self.energy_threshold = energy_threshold
        self.min_speech_ms = min_speech_ms
        self.min_silence_ms = min_silence_ms
        self.speech_pad_ms = speech_pad_ms

    def detect_intervals(
        self,
        samples: np.ndarray,
        sample_rate: int = 16000,
    ) -> List[SpeechInterval]:
        """Detects speech intervals in seconds across the audio signal.

        Args:
            samples: 1D float32 audio samples array.
            sample_rate: Audio sample rate in Hz (default: 16000).

        Returns:
            List of SpeechInterval objects with start and end times in seconds.
        """
        if len(samples) == 0:
            return []

        frame_size = int(sample_rate * (self.frame_ms / 1000.0))
        num_frames = len(samples) // frame_size

        if num_frames == 0:
            return [SpeechInterval(start=0.0, end=len(samples) / float(sample_rate))]

        # Calculate RMS energy for each frame
        rms_energies = np.zeros(num_frames, dtype=np.float32)
        for i in range(num_frames):
            frame = samples[i * frame_size : (i + 1) * frame_size]
            rms_energies[i] = np.sqrt(np.mean(frame**2) + 1e-12)

        # Dynamic noise floor estimation (15th percentile energy)
        noise_floor = float(np.percentile(rms_energies, 15))
        adaptive_threshold = max(self.energy_threshold, noise_floor * 2.2)

        frame_is_speech = rms_energies > adaptive_threshold

        # Group contiguous speech frames with hysteresis
        raw_intervals: List[Tuple[int, int]] = []
        in_speech = False
        start_frame = 0

        for idx, active in enumerate(frame_is_speech):
            if active and not in_speech:
                in_speech = True
                start_frame = idx
            elif not active and in_speech:
                in_speech = False
                raw_intervals.append((start_frame, idx))

        if in_speech:
            raw_intervals.append((start_frame, num_frames))

        if not raw_intervals:
            # Low overall energy; return entire audio rather than dropping content
            total_duration = len(samples) / float(sample_rate)
            return [SpeechInterval(start=0.0, end=round(total_duration, 2))]

        # Merge segments separated by less than min_silence_ms
        min_silence_frames = int((self.min_silence_ms / 1000.0) / (self.frame_ms / 1000.0))
        merged_intervals: List[Tuple[int, int]] = []

        curr_start, curr_end = raw_intervals[0]
        for next_start, next_end in raw_intervals[1:]:
            if (next_start - curr_end) < min_silence_frames:
                # Merge because gap is smaller than min_silence
                curr_end = next_end
            else:
                merged_intervals.append((curr_start, curr_end))
                curr_start, curr_end = next_start, next_end
        merged_intervals.append((curr_start, curr_end))

        # Filter out intervals shorter than min_speech_ms, apply padding
        pad_seconds = self.speech_pad_ms / 1000.0
        min_speech_seconds = self.min_speech_ms / 1000.0
        total_duration = len(samples) / float(sample_rate)

        final_intervals: List[SpeechInterval] = []
        for start_f, end_f in merged_intervals:
            start_sec = max(0.0, (start_f * frame_size / float(sample_rate)) - pad_seconds)
            end_sec = min(total_duration, (end_f * frame_size / float(sample_rate)) + pad_seconds)

            if (end_sec - start_sec) >= min_speech_seconds:
                final_intervals.append(
                    SpeechInterval(start=round(start_sec, 2), end=round(end_sec, 2))
                )

        return final_intervals if final_intervals else [
            SpeechInterval(start=0.0, end=round(total_duration, 2))
        ]


def get_vad_parameters_dict() -> Dict[str, Any]:
    """Returns tuned Silero VAD parameters for faster-whisper pipeline.

    Carefully configured for classroom lectures:
    - speech_pad_ms: 400ms prevents consonant truncation.
    - min_silence_duration_ms: 500ms avoids fracturing natural pedagogical pauses.
    - threshold: 0.5 balanced speech sensitivity.
    """
    return {
        "threshold": 0.5,
        "min_speech_duration_ms": 250,
        "max_speech_duration_s": 30.0,
        "min_silence_duration_ms": 500,
        "speech_pad_ms": 400,
    }
