#!/usr/bin/env python3
"""Script to download multilingual ASR models for offline GyanDrishti execution.

Usage:
    python backend/scripts/download_model.py [--model small] [--dest /path/to/models]
"""

import argparse
import sys
from pathlib import Path

# Add backend directory to sys.path so speech_engine can be imported directly
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from speech_engine.models import (
    AVAILABLE_MODELS,
    DEFAULT_MODEL_NAME,
    download_model,
    is_model_downloaded,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download Whisper models for GyanDrishti offline speech engine"
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=DEFAULT_MODEL_NAME,
        choices=list(AVAILABLE_MODELS.keys()),
        help=f"Model name to download (default: {DEFAULT_MODEL_NAME})",
    )
    parser.add_argument(
        "--dest", "-d",
        type=str,
        default=None,
        help="Custom destination directory for models (default: backend/models/)",
    )

    args = parser.parse_args()
    target_dir = Path(args.dest) if args.dest else None

    print("=" * 65)
    print("  GyanDrishti Model Pre-Downloader (Offline Foundation)")
    print("=" * 65)
    meta = AVAILABLE_MODELS[args.model]
    print(f"Target Model:      {args.model}")
    print(f"HuggingFace Repo:  {meta.hf_repo}")
    print(f"Approx Disk Size:  {meta.disk_size_mb} MB")
    print(f"Approx RAM Usage:  ~{meta.approx_ram_mb} MB")
    print(f"Indic Accuracy:    {meta.indic_accuracy}")
    print("=" * 65)

    if is_model_downloaded(args.model, target_dir):
        print(f"\n[OK] Model '{args.model}' is ALREADY fully downloaded and available locally.")
        print("You can turn off Wi-Fi/Internet completely and run offline transcription.")
        return

    print(f"\nDownloading weights for '{args.model}' into local storage...")
    try:
        model_path = download_model(model_name=args.model, target_dir=target_dir)
        print(f"\n[SUCCESS] Model downloaded successfully to:\n  {model_path}")
        print("\nVerification Checklist:")
        print("  1. Weight files exist locally in backend/models/")
        print("  2. Disconnect Wi-Fi / turn off network")
        print("  3. Run: python -m speech_engine transcribe <audio.wav> --offline")
        print("  4. Verify transcription completes without network calls.")
    except Exception as e:
        print(f"\n[FAILED] Model download error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
