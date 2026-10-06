#!/usr/bin/env python3
"""ASR Benchmarking Suite for GyanDrishti.

Evaluates:
- Audio duration
- Processing time
- Real-Time Factor (RTF = processing_time / audio_duration)
- Detected languages & script preservation
- Transcription output
- Segment count and silence filtering

Outputs summary table and structured JSON report.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Add backend directory to sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from speech_engine.models import AVAILABLE_MODELS, DEFAULT_MODEL_NAME
from speech_engine.transcription import transcribe_file


def run_benchmark(
    audio_paths: List[Path],
    model_name: str = DEFAULT_MODEL_NAME,
    language: str | None = None,
    output_report_path: Path | None = None,
    offline_only: bool = False,
) -> Dict[str, Any]:
    """Runs ASR benchmark over a list of audio files."""
    results: List[Dict[str, Any]] = []
    total_audio_duration = 0.0
    total_processing_time = 0.0

    print("=" * 80)
    print(f"  GyanDrishti ASR Benchmark (Model: {model_name})")
    print("=" * 80)
    fmt_header = "{:<3} {:<24} {:<10} {:<10} {:<8} {:<10} {:<12}"
    print(fmt_header.format("#", "Filename", "Audio(s)", "Time(s)", "RTF", "Langs", "Segments"))
    print("-" * 80)

    for idx, audio_path in enumerate(audio_paths, start=1):
        try:
            res = transcribe_file(
                file_path=audio_path,
                model_name=model_name,
                language=language,
                offline_only=offline_only,
            )

            total_audio_duration += res.duration
            total_processing_time += res.processing_time

            langs_str = ",".join(res.language_summary) if res.language_summary else "none"
            print(
                fmt_header.format(
                    idx,
                    audio_path.name[:23],
                    f"{res.duration:.2f}",
                    f"{res.processing_time:.2f}",
                    f"{res.real_time_factor:.3f}",
                    langs_str,
                    len(res.segments),
                )
            )

            # Store result item
            json_out = audio_path.with_suffix(".json")
            res.save_json(json_out)

            results.append({
                "filename": audio_path.name,
                "file_path": str(audio_path),
                "audio_duration_seconds": res.duration,
                "processing_time_seconds": res.processing_time,
                "real_time_factor": res.real_time_factor,
                "detected_languages": res.language_summary,
                "segment_count": len(res.segments),
                "transcript_preview": res.raw_text[:120] + "..." if len(res.raw_text) > 120 else res.raw_text,
                "output_json_path": str(json_out),
            })
        except Exception as e:
            print(f"  [{idx}] ERROR processing {audio_path.name}: {e}", file=sys.stderr)
            results.append({
                "filename": audio_path.name,
                "file_path": str(audio_path),
                "error": str(e),
            })

    print("-" * 80)
    overall_rtf = (
        (total_processing_time / total_audio_duration)
        if total_audio_duration > 0
        else 0.0
    )
    print(f"  TOTAL AUDIO DURATION:     {total_audio_duration:.2f} s")
    print(f"  TOTAL PROCESSING TIME:    {total_processing_time:.2f} s")
    print(f"  OVERALL REAL-TIME FACTOR: {overall_rtf:.3f} (RTF < 1.0 means faster than real-time)")
    print("=" * 80)

    report_payload: Dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model_name": model_name,
        "total_files": len(audio_paths),
        "total_audio_duration_seconds": round(total_audio_duration, 2),
        "total_processing_time_seconds": round(total_processing_time, 2),
        "overall_real_time_factor": round(overall_rtf, 3),
        "benchmark_results": results,
    }

    if output_report_path:
        output_report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_report_path, "w", encoding="utf-8") as f:
            json.dump(report_payload, f, indent=2, ensure_ascii=False)
        print(f"\n>> Benchmark report written to: {output_report_path}")

    return report_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark GyanDrishti Multilingual ASR Engine")
    parser.add_argument(
        "files",
        nargs="*",
        help="One or more audio files to benchmark",
    )
    parser.add_argument(
        "--dir", "-d",
        type=str,
        default=None,
        help="Directory containing audio files to benchmark",
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=DEFAULT_MODEL_NAME,
        choices=list(AVAILABLE_MODELS.keys()),
        help=f"Whisper model size to evaluate (default: {DEFAULT_MODEL_NAME})",
    )
    parser.add_argument(
        "--language", "-l",
        type=str,
        default=None,
        help="Force language (e.g. 'en', 'hi', 'bn') or None for auto",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Path to save benchmark JSON report",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Enforce offline operation",
    )

    args = parser.parse_args()

    # Collect audio files
    paths: List[Path] = []
    if args.files:
        for f in args.files:
            p = Path(f)
            if p.is_file():
                paths.append(p)
            else:
                print(f"[WARNING] Skipping non-existent file: {p}", file=sys.stderr)

    if args.dir:
        dir_path = Path(args.dir)
        if dir_path.is_dir():
            for ext in ("*.wav", "*.mp3", "*.m4a", "*.flac"):
                paths.extend(dir_path.glob(ext))

    if not paths:
        print("[ERROR] No audio files provided. Pass file paths or use --dir <recordings_directory>.", file=sys.stderr)
        print("Example: python backend/benchmarks/benchmark_asr.py backend/recordings/*.wav", file=sys.stderr)
        sys.exit(1)

    out_report = Path(args.output) if args.output else backend_root / "benchmarks" / "benchmark_report.json"
    run_benchmark(
        audio_paths=paths,
        model_name=args.model,
        language=args.language,
        output_report_path=out_report,
        offline_only=args.offline,
    )


if __name__ == "__main__":
    main()
