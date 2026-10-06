"""Command Line Interface for GyanDrishti Speech Engine.

Supports recording from microphone, transcribing local audio files, downloading
models for offline use, and listing hardware devices.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from speech_engine.audio import list_microphones
from speech_engine.models import (
    AVAILABLE_MODELS,
    DEFAULT_MODEL_NAME,
    download_model,
    is_model_downloaded,
)
from speech_engine.transcription import (
    transcribe_file,
    transcribe_microphone,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("speech_engine.cli")


def _print_banner() -> None:
    banner = r"""
======================================================================
  GyanDrishti (ज्ञान दृष्टि / জ্ঞান দৃষ্টি) Speech Engine
  Offline Multilingual Intelligence (en / hi / bn)
======================================================================
"""
    print(banner)


def _display_transcription_result(result) -> None:
    """Pretty prints the structured transcription result to console."""
    print("\n" + "=" * 70)
    print(f"  TRANSCRIPTION SUMMARY")
    print("=" * 70)
    print(f"  Model:           {result.model_name} (compute_type: {result.compute_type}, device: {result.device})")
    print(f"  Audio Duration:  {result.duration:.2f} seconds")
    print(f"  Processing Time: {result.processing_time:.2f} seconds")
    print(f"  Real-Time Factor (RTF): {result.real_time_factor:.3f} (lower is faster)")
    print(f"  Languages Found: {', '.join(result.language_summary) if result.language_summary else 'None'}")
    print("=" * 70)

    print("\n  TIMESTAMPED SEGMENTS:")
    print("-" * 70)
    if not result.segments:
        print("  (No speech segments detected)")
    else:
        for seg in result.segments:
            time_range = f"[{seg.start:6.2f}s -> {seg.end:6.2f}s]"
            langs = f"[{','.join(seg.language)}]"
            print(f"  {time_range}  {langs:<12} {seg.text}")
    print("-" * 70)

    print("\n  RAW TEXT (PRESERVED SOURCE DATA):")
    print(f"  {result.raw_text if result.raw_text else '(empty)'}\n")


def cmd_record(args: argparse.Namespace) -> int:
    """Handles the 'record' CLI subcommand."""
    _print_banner()
    duration = args.duration
    model = args.model
    lang = args.language
    no_vad = args.no_vad

    print(f">> Initializing microphone recording (max duration: {duration:.0f}s)...")
    print(f">> Model: {model} | Language: {lang or 'Auto'} | VAD: {not no_vad} | Offline: {args.offline}")
    print(">> Speak into your microphone now.")
    print(">> TIP: Press [Ctrl+C] at any time to finish speaking and begin transcription immediately.\n")

    timestamp_str = time.strftime("%Y%m%d_%H%M%S")
    backend_root = Path(__file__).resolve().parent.parent

    # Default audio path
    if args.output_audio:
        audio_path = Path(args.output_audio)
    else:
        recordings_dir = backend_root / "recordings"
        audio_path = recordings_dir / f"recording_{timestamp_str}.wav"

    # Default json path
    if args.output_json:
        json_path = Path(args.output_json)
    else:
        recordings_dir = backend_root / "recordings"
        json_path = recordings_dir / f"transcript_{timestamp_str}.json"

    try:
        result = transcribe_microphone(
            duration=duration,
            output_audio_path=audio_path,
            output_json_path=json_path,
            model_name=model,
            language=lang,
            vad=not no_vad,
            device_id=args.device,
            offline_only=args.offline,
        )
    except PermissionError as e:
        print(f"\n[ERROR: Microphone Permission Denied]\n{e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n[ERROR: Recording/ASR failed]\n{e}", file=sys.stderr)
        return 1

    _display_transcription_result(result)
    print(f">> Audio recording saved to: {audio_path}")
    print(f">> Transcript JSON saved to: {json_path}")
    return 0


def cmd_transcribe(args: argparse.Namespace) -> int:
    """Handles the 'transcribe' CLI subcommand."""
    _print_banner()
    input_file = Path(args.audio_file)
    if not input_file.is_file():
        print(f"[ERROR] Audio file not found: {input_file}", file=sys.stderr)
        return 1

    model = args.model
    lang = args.language
    no_vad = args.no_vad

    print(f">> Transcribing audio file: {input_file}")
    print(f">> Model: {model} | Language: {lang or 'Auto'} | VAD: {not no_vad}")

    try:
        result = transcribe_file(
            file_path=input_file,
            model_name=model,
            language=lang,
            vad=not no_vad,
            offline_only=args.offline,
        )
    except Exception as e:
        print(f"\n[ERROR: Transcription failed]\n{e}", file=sys.stderr)
        return 1

    _display_transcription_result(result)

    if args.output_json:
        out_json = Path(args.output_json)
    else:
        out_json = input_file.with_suffix(".json")

    result.save_json(out_json)
    print(f">> Structured transcript saved to: {out_json}")
    return 0


def cmd_download(args: argparse.Namespace) -> int:
    """Handles downloading models for offline operation."""
    _print_banner()
    model_name = args.model
    print(f">> Downloading model '{model_name}' for local offline use...")

    try:
        path = download_model(model_name=model_name)
        print(f"\n[SUCCESS] Model '{model_name}' is downloaded and ready at:\n  {path}")
        print("You can now safely run GyanDrishti completely offline without internet.")
        return 0
    except Exception as e:
        print(f"\n[ERROR] Failed to download model: {e}", file=sys.stderr)
        return 1


def cmd_models(args: argparse.Namespace) -> int:
    """Lists available models, specifications, and local download status."""
    _print_banner()
    print("Available ASR Models for GyanDrishti:\n")
    fmt = "{:<16} {:<12} {:<12} {:<10} {:<30}"
    print(fmt.format("Model", "Disk Size", "RAM Usage", "Offline", "Indic Accuracy"))
    print("-" * 80)
    for name, meta in AVAILABLE_MODELS.items():
        is_dl = "YES (Ready)" if is_model_downloaded(name) else "NO"
        rec = " [DEFAULT]" if name == DEFAULT_MODEL_NAME else ""
        print(fmt.format(
            f"{name}{rec}",
            f"{meta.disk_size_mb} MB",
            f"~{meta.approx_ram_mb} MB",
            is_dl,
            meta.indic_accuracy,
        ))
    print("\nNote: 'small' is recommended for Apple Silicon M2 (8 GB RAM).")
    return 0


def cmd_devices(args: argparse.Namespace) -> int:
    """Lists available microphone input devices."""
    _print_banner()
    print("Available Audio Input Devices (Microphones):\n")
    devs = list_microphones()
    if not devs:
        print("No input devices detected.")
        return 0
    for dev in devs:
        print(f"  [ID {dev['id']}] {dev['name']} ({dev['channels']} channel(s), {dev['default_sr']} Hz)")
    print()
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Builds the main argument parser for CLI."""
    parser = argparse.ArgumentParser(
        prog="python -m speech_engine",
        description="GyanDrishti Multilingual Speech Engine (Milestone 1)",
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Command: record
    rec_parser = subparsers.add_parser("record", help="Record from microphone and transcribe")
    rec_parser.add_argument(
        "--duration", "-d",
        type=float,
        default=30.0,
        help="Recording duration in seconds (default: 30.0s)",
    )
    rec_parser.add_argument(
        "--model", "-m",
        type=str,
        default=DEFAULT_MODEL_NAME,
        choices=list(AVAILABLE_MODELS.keys()),
        help=f"ASR model to use (default: {DEFAULT_MODEL_NAME})",
    )
    rec_parser.add_argument(
        "--language", "-l",
        type=str,
        default=None,
        help="Force language ('en', 'hi', 'bn') or leave blank for auto-detection",
    )
    rec_parser.add_argument(
        "--output-audio", "-oa",
        type=str,
        default=None,
        help="Custom path to save recorded WAV file",
    )
    rec_parser.add_argument(
        "--output-json", "-oj",
        type=str,
        default=None,
        help="Custom path to save transcript JSON",
    )
    rec_parser.add_argument(
        "--device",
        type=int,
        default=None,
        help="Microphone device ID (see: python -m speech_engine devices)",
    )
    rec_parser.add_argument(
        "--no-vad",
        action="store_true",
        help="Disable Voice Activity Detection silence filtering",
    )
    rec_parser.add_argument(
        "--offline",
        action="store_true",
        help="Enforce strictly offline execution; fail if model not locally stored",
    )

    # Command: transcribe
    ts_parser = subparsers.add_parser("transcribe", help="Transcribe an existing audio file (WAV, MP3, M4A)")
    ts_parser.add_argument(
        "audio_file",
        type=str,
        help="Path to audio file",
    )
    ts_parser.add_argument(
        "--model", "-m",
        type=str,
        default=DEFAULT_MODEL_NAME,
        choices=list(AVAILABLE_MODELS.keys()),
        help=f"ASR model to use (default: {DEFAULT_MODEL_NAME})",
    )
    ts_parser.add_argument(
        "--language", "-l",
        type=str,
        default=None,
        help="Force language ('en', 'hi', 'bn') or leave blank for auto-detection",
    )
    ts_parser.add_argument(
        "--output-json", "-oj",
        type=str,
        default=None,
        help="Custom path to save output JSON",
    )
    ts_parser.add_argument(
        "--no-vad",
        action="store_true",
        help="Disable Voice Activity Detection silence filtering",
    )
    ts_parser.add_argument(
        "--offline",
        action="store_true",
        help="Enforce strictly offline execution; fail if model not locally stored",
    )

    # Command: download
    dl_parser = subparsers.add_parser("download", help="Pre-download ASR model weights for offline operation")
    dl_parser.add_argument(
        "--model", "-m",
        type=str,
        default=DEFAULT_MODEL_NAME,
        choices=list(AVAILABLE_MODELS.keys()),
        help=f"Model to download (default: {DEFAULT_MODEL_NAME})",
    )

    # Command: models
    subparsers.add_parser("models", help="List available models and download status")

    # Command: devices
    subparsers.add_parser("devices", help="List audio input devices (microphones)")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "record": cmd_record,
        "transcribe": cmd_transcribe,
        "download": cmd_download,
        "models": cmd_models,
        "devices": cmd_devices,
    }

    handler = dispatch.get(args.command)
    if handler:
        sys.exit(handler(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
