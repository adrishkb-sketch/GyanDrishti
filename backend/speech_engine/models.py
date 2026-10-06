"""Model registry and offline storage manager for GyanDrishti Speech Engine.

Manages offline model storage under `backend/models/`, providing hardware-optimized
configurations for Apple Silicon (M-series) with 8 GB RAM.
"""

from __future__ import annotations

import logging
import os
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Default root directory for storing offline model weights
DEFAULT_MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


@dataclass(frozen=True)
class ModelMetadata:
    """Metadata describing model characteristics, memory footprint, and capabilities."""

    name: str
    hf_repo: str
    disk_size_mb: int
    approx_ram_mb: int
    indic_accuracy: str  # "Basic", "Strong", "State-of-the-art"
    recommended_for_m2_8gb: bool
    description: str


AVAILABLE_MODELS: Dict[str, ModelMetadata] = {
    "tiny": ModelMetadata(
        name="tiny",
        hf_repo="Systran/faster-whisper-tiny",
        disk_size_mb=75,
        approx_ram_mb=250,
        indic_accuracy="Low / experimental (poor script preservation)",
        recommended_for_m2_8gb=False,
        description="Fastest model, low resource usage, but prone to high word error rate on Hindi/Bengali.",
    ),
    "base": ModelMetadata(
        name="base",
        hf_repo="Systran/faster-whisper-base",
        disk_size_mb=145,
        approx_ram_mb=450,
        indic_accuracy="Moderate (acceptable for simple speech)",
        recommended_for_m2_8gb=True,
        description="Ultra-lightweight option. Fast on M2, reasonable for basic English and simple Hindi.",
    ),
    "small": ModelMetadata(
        name="small",
        hf_repo="Systran/faster-whisper-small",
        disk_size_mb=485,
        approx_ram_mb=900,
        indic_accuracy="Strong (recommended default for Hindi, Bengali, and English)",
        recommended_for_m2_8gb=True,
        description="Best tradeoff for GyanDrishti Milestone 1. Excellent script preservation for Devanagari & Bangla.",
    ),
    "medium": ModelMetadata(
        name="medium",
        hf_repo="Systran/faster-whisper-medium",
        disk_size_mb=1530,
        approx_ram_mb=2200,
        indic_accuracy="High (rich vocabulary)",
        recommended_for_m2_8gb=False,
        description="High accuracy but consumes >2 GB RAM, closer to memory limit on 8 GB machines.",
    ),
    "large-v3-turbo": ModelMetadata(
        name="large-v3-turbo",
        hf_repo="Systran/faster-whisper-large-v3-turbo",
        disk_size_mb=1620,
        approx_ram_mb=2500,
        indic_accuracy="State-of-the-art",
        recommended_for_m2_8gb=False,
        description="Highest accuracy across all Indic dialects, but higher RAM pressure on 8 GB hardware.",
    ),
}

DEFAULT_MODEL_NAME = "small"


def is_apple_silicon() -> bool:
    """Returns True if running on Apple Silicon (arm64 macOS)."""
    return sys.platform == "darwin" and platform.machine() == "arm64"


def get_optimal_compute_type() -> str:
    """Selects the optimal CTranslate2 compute type for current hardware.

    On Apple Silicon (M1/M2/M3), 'int8' leverages ARM NEON vector instructions
    providing up to 4x throughput with minimal RAM usage.
    """
    return "int8"


def get_model_dir(model_name: str, base_dir: Optional[Path] = None) -> Path:
    """Returns the local directory path for a model."""
    root = base_dir or DEFAULT_MODELS_DIR
    return root / model_name


def is_model_downloaded(model_name: str, base_dir: Optional[Path] = None) -> bool:
    """Checks whether the requested model files exist locally in the models directory."""
    model_dir = get_model_dir(model_name, base_dir)
    if not model_dir.is_dir():
        return False
    # A valid CTranslate2 Whisper model contains model.bin and config.json
    model_bin = model_dir / "model.bin"
    config_json = model_dir / "config.json"
    return model_bin.is_file() and config_json.is_file()


def download_model(
    model_name: str = DEFAULT_MODEL_NAME,
    target_dir: Optional[Path] = None,
) -> Path:
    """Downloads model weights to the local models directory for offline operation.

    Args:
        model_name: Name of model ('tiny', 'base', 'small', 'medium', 'large-v3-turbo').
        target_dir: Root directory for models (default: backend/models/).

    Returns:
        Path to the downloaded model directory.
    """
    if model_name not in AVAILABLE_MODELS:
        raise ValueError(
            f"Unknown model '{model_name}'. Choose from: {list(AVAILABLE_MODELS.keys())}"
        )

    dest = get_model_dir(model_name, target_dir)
    dest.mkdir(parents=True, exist_ok=True)

    if is_model_downloaded(model_name, target_dir):
        logger.info("Model '%s' is already downloaded at: %s", model_name, dest)
        return dest

    meta = AVAILABLE_MODELS[model_name]
    logger.info(
        "Downloading model '%s' from %s to %s (approx %d MB)...",
        model_name, meta.hf_repo, dest, meta.disk_size_mb
    )

    from huggingface_hub import snapshot_download

    snapshot_download(
        repo_id=meta.hf_repo,
        local_dir=str(dest),
        local_dir_use_symlinks=False,
    )

    logger.info("Successfully downloaded '%s' to %s", model_name, dest)
    return dest
