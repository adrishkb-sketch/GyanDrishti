"""Audio input and preprocessing abstraction for GyanDrishti Speech Engine.

Handles audio loading, format conversion (WAV, MP3, M4A), normalization,
resampling to standard 16 kHz mono float32, and microphone recording.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Union

import numpy as np
import sounddevice as sd
import soundfile as sf

logger = logging.getLogger(__name__)

STANDARD_SAMPLE_RATE = 16000  # 16 kHz expected by Whisper / modern ASR models


@dataclass
class AudioInput:
    """Standardized representation of audio ready for ASR processing."""

    samples: np.ndarray  # 1D float32 array in range [-1.0, 1.0]
    sample_rate: int = STANDARD_SAMPLE_RATE
    duration: float = 0.0

    def __post_init__(self) -> None:
        if self.duration == 0.0 and len(self.samples) > 0:
            self.duration = len(self.samples) / float(self.sample_rate)


def normalize_audio(samples: np.ndarray, target_peak: float = 0.95) -> np.ndarray:
    """Normalizes peak amplitude of audio samples to prevent clipping and enhance faint speech.

    Args:
        samples: 1D float32 numpy array.
        target_peak: Target peak amplitude (default: 0.95).

    Returns:
        Normalized 1D float32 array.
    """
    if samples.size == 0:
        return samples

    samples = samples.astype(np.float32)
    max_peak = float(np.max(np.abs(samples)))

    if max_peak > 1e-6:
        samples = (samples / max_peak) * target_peak
    return np.clip(samples, -1.0, 1.0)


def resample_linear(samples: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """High-quality 1D linear interpolation resampler avoiding external heavy resampler dependencies."""
    if orig_sr == target_sr:
        return samples
    if samples.size == 0:
        return samples

    num_target_samples = int(round(len(samples) * float(target_sr) / float(orig_sr)))
    orig_indices = np.linspace(0, len(samples) - 1, num=len(samples), endpoint=True)
    target_indices = np.linspace(0, len(samples) - 1, num=num_target_samples, endpoint=True)
    return np.interp(target_indices, orig_indices, samples).astype(np.float32)


def _load_audio_via_ffmpeg(file_path: Path, target_sr: int = STANDARD_SAMPLE_RATE) -> np.ndarray:
    """Decodes non-standard formats (MP3, M4A, AAC) using local FFmpeg binary."""
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        raise RuntimeError(
            f"FFmpeg is required to decode {file_path.suffix} files, but ffmpeg was not found in PATH."
        )

    cmd = [
        ffmpeg_bin,
        "-nostdin",
        "-threads", "0",
        "-i", str(file_path),
        "-f", "s16le",
        "-ac", "1",
        "-ar", str(target_sr),
        "-"
    ]

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"FFmpeg failed to decode {file_path}: {err_msg}") from e

    # Convert 16-bit PCM bytes to float32 array in range [-1.0, 1.0]
    audio_int16 = np.frombuffer(proc.stdout, dtype=np.int16)
    audio_float = audio_int16.astype(np.float32) / 32768.0
    return audio_float


def load_audio(
    file_path: Union[str, Path],
    target_sr: int = STANDARD_SAMPLE_RATE,
    normalize: bool = True,
) -> AudioInput:
    """Loads an audio file (WAV, MP3, M4A, etc.), converts to mono 16 kHz float32.

    Args:
        file_path: Path to the target audio file.
        target_sr: Target sample rate (default 16000).
        normalize: Whether to apply peak normalization.

    Returns:
        AudioInput object with samples, sample rate, and duration.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Audio file not found: {path}")

    # Primary attempt using soundfile (supports WAV, FLAC, OGG)
    samples: np.ndarray
    try:
        data, orig_sr = sf.read(str(path), dtype="float32")
        # Convert multi-channel to mono
        if data.ndim > 1:
            data = np.mean(data, axis=1)
        # Resample if necessary
        if orig_sr != target_sr:
            samples = resample_linear(data, orig_sr, target_sr)
        else:
            samples = data
    except Exception as sf_err:
        logger.info("soundfile failed to read %s (%s). Attempting FFmpeg fallback.", path, sf_err)
        samples = _load_audio_via_ffmpeg(path, target_sr=target_sr)

    if normalize:
        samples = normalize_audio(samples)

    duration = float(len(samples)) / float(target_sr) if len(samples) > 0 else 0.0
    return AudioInput(samples=samples, sample_rate=target_sr, duration=duration)


def save_wav(
    file_path: Union[str, Path],
    samples: np.ndarray,
    sample_rate: int = STANDARD_SAMPLE_RATE,
) -> Path:
    """Saves float32 audio samples as a 16-bit standard PCM WAV file.

    Args:
        file_path: Target destination path.
        samples: 1D numpy array of audio samples.
        sample_rate: Sample rate (default 16000).

    Returns:
        Path to the saved WAV file.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure audio is float32 and in valid range
    clipped = np.clip(samples, -1.0, 1.0)
    sf.write(str(path), clipped, sample_rate, subtype="PCM_16")
    return path


def list_microphones() -> List[dict[str, Union[int, str]]]:
    """Lists available audio input devices."""
    devices = sd.query_devices()
    input_devs: List[dict[str, Union[int, str]]] = []
    for idx, dev in enumerate(devices):
        if dev.get("max_input_channels", 0) > 0:
            input_devs.append({
                "id": idx,
                "name": str(dev.get("name", "Unknown")),
                "channels": int(dev.get("max_input_channels", 1)),
                "default_sr": float(dev.get("default_samplerate", 44100)),
            })
    return input_devs


def record_microphone(
    duration: float,
    sample_rate: int = STANDARD_SAMPLE_RATE,
    device_id: Optional[int] = None,
    normalize: bool = True,
) -> AudioInput:
    """Records audio from the microphone for a fixed duration.

    Args:
        duration: Duration to record in seconds.
        sample_rate: Recording sample rate (default 16000).
        device_id: Audio input device ID (default None selects system default).
        normalize: Whether to peak-normalize the recorded audio.

    Returns:
        AudioInput object.
    """
    if duration <= 0:
        raise ValueError(f"Duration must be greater than 0, got {duration}")

    logger.info("Starting microphone recording (up to %.1f seconds, press Ctrl+C to finish)...", duration)
    chunks: List[np.ndarray] = []

    def audio_callback(indata: np.ndarray, frames: int, time_info: dict, status: sd.CallbackFlags) -> None:
        if status:
            logger.warning("Microphone callback status: %s", status)
        chunks.append(indata.copy())

    start_time = time.time()
    try:
        with sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
            device=device_id,
            callback=audio_callback,
        ):
            while time.time() - start_time < duration:
                time.sleep(0.1)
    except KeyboardInterrupt:
        logger.info("Microphone recording ended by user.")
    except sd.PortAudioError as e:
        error_msg = str(e)
        if "permission" in error_msg.lower() or "device unavailable" in error_msg.lower():
            raise PermissionError(
                "Microphone access denied or audio device unavailable. "
                "On macOS, verify microphone permissions in: "
                "System Settings -> Privacy & Security -> Microphone -> Terminal / Python."
            ) from e
        raise RuntimeError(f"Audio recording failed: {error_msg}") from e

    if not chunks:
        samples = np.zeros(0, dtype=np.float32)
    else:
        samples = np.concatenate(chunks, axis=0).flatten()

    if normalize and len(samples) > 0:
        samples = normalize_audio(samples)

    return AudioInput(
        samples=samples,
        sample_rate=sample_rate,
        duration=float(len(samples)) / float(sample_rate) if len(samples) > 0 else 0.0,
    )
