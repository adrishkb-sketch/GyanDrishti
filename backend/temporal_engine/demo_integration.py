import json
from pathlib import Path
import sys

backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from temporal_engine.timeline import create_lecture_timeline

# 1. Real speech transcription from Milestone 1 human recording test
speech_json_path = backend_root / "recordings" / "validation_test.json"

# 2. Real video session manifest from Milestone 2 device capture test
manifest_candidates = sorted(list(backend_root.glob("**/manifests/lecture_*.json")), reverse=True)
if not manifest_candidates:
    raise FileNotFoundError("No video manifests found under backend/")

video_manifest_path = manifest_candidates[0]
for p in manifest_candidates:
    try:
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
            if len(d.get("events", [])) > 0:
                video_manifest_path = p
                break
    except Exception:
        continue

print("=" * 80)
print("  GyanDrishti Milestone 3: Temporal Fusion Integration Demo")
print("=" * 80)
print(f"Loading speech transcript: {speech_json_path}")
print(f"Loading video manifest:    {video_manifest_path}\n")

# Run temporal fusion
timeline = create_lecture_timeline(
    speech_source=speech_json_path,
    visual_source=video_manifest_path,
    lecture_id="demo_lecture_fusion_01",
    window_before=5.0,
    window_after=5.0,
)

print(f"Unified Timeline Created!")
print(f"  Lecture ID:              {timeline.lecture_id}")
print(f"  Calculated Duration:     {timeline.duration:.2f}s")
print(f"  Total Speech Segments:   {timeline.total_speech_events}")
print(f"  Total Visual Events:     {timeline.total_visual_events}")
print(f"  Chronological Stream:    {len(timeline.chronological_stream)} events")
print(f"  Synchronized Clusters:   {len(timeline.synchronized_events)} multimodal block(s)\n")

print("-" * 80)
print("CHRONOLOGICAL STREAM PREVIEW (Linear Timeline):")
print("-" * 80)
for evt in timeline.chronological_stream[:6]:
    if evt.type == "speech":
        print(f"  [{evt.timestamp:5.2f}s] [SPEECH] \"{evt.data.get('text')[:60]}...\"")
    else:
        print(f"  [{evt.timestamp:5.2f}s] [{evt.source.upper()} KEYFRAME] path: {evt.data.get('frame_path')} (score: {evt.data.get('change_score')})")

print("\n" + "-" * 80)
print("SYNCHRONIZED MULTIMODAL BLOCK (Speech + Visual Association):")
print("-" * 80)
for idx, block in enumerate(timeline.synchronized_events, start=1):
    print(f"\n[Synchronized Block #{idx}] Time window: {block.start:.2f}s -> {block.end:.2f}s")
    print(f"  Speech Content ({len(block.speech)} segment):")
    for s in block.speech:
        print(f"    - [{s.start:.2f}s - {s.end:.2f}s] \"{s.text}\" (Langs: {s.language})")
    print(f"  Associated Visual Events ({len(block.visual_events)} keyframe/event(s)):")
    for v in block.visual_events[:3]:
        print(f"    - [{v.timestamp:.2f}s] [{v.source}] score={v.change_score} -> {v.frame_path}")
    if len(block.visual_events) > 3:
        print(f"    ... and {len(block.visual_events) - 3} more visual event(s)")

# Export sample output to json
out_path = backend_root / "temporal_engine" / "sample_fused_timeline.json"
timeline.save_json(out_path)
print(f"\nSaved fused timeline to: {out_path}")
print("=" * 80)
