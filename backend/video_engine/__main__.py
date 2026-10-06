import argparse
import sys
import time
import os
from datetime import datetime

from .capture.camera import CameraCapture, list_cameras
from .capture.screen import ScreenCapture, list_displays
from .storage.video_writer import LocalVideoWriter
from .frames.sampler import FrameSampler
from .frames.change_detector import ChangeDetector
from .frames.keyframes import KeyframeExtractor
from .storage.manifest import ManifestGenerator
from .schemas import Manifest

def cmd_devices(args):
    print("CAMERAS:")
    cams = list_cameras()
    if not cams:
        print("  No cameras detected.")
    else:
        for c in cams:
            print(f"  - Device ID {c}")
            
    print("\nDISPLAYS:")
    displays = list_displays()
    for i, d in enumerate(displays):
        print(f"  - Display ID {i+1}: {d['width']}x{d['height']}")

def _record_loop(sources, duration, fps=10):
    writers = {}
    session_id = f"lecture_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    for s in sources:
        out_path = f"backend/video_engine/recordings/{s.source_name}/{session_id}.mp4"
        writers[s.source_name] = LocalVideoWriter(out_path, fps=fps)
    
    sampler = FrameSampler(target_fps=2.0)
    detectors = {s.source_name: ChangeDetector(threshold=0.05) for s in sources}
    extractor = KeyframeExtractor()
    events = []
    
    start_time = time.time()
    print(f"Recording for {duration} seconds... Session: {session_id}")
    
    try:
        while time.time() - start_time < duration:
            now = time.time()
            for src in sources:
                frame, meta = src.read_frame()
                if frame is not None:
                    writers[src.source_name].write(frame)
                    
                    if sampler.should_sample(now):
                        score, is_changed = detectors[src.source_name].check_change(frame)
                        if is_changed:
                            evt = extractor.save_keyframe(frame, meta, score, "visual_change")
                            events.append(evt)
            time.sleep(1.0 / fps)
    except KeyboardInterrupt:
        print("Recording stopped manually.")
    finally:
        for src in sources:
            src.release()
            writers[src.source_name].release()
            
        manifest = Manifest(
            session_id=session_id,
            start_time=datetime.fromtimestamp(start_time).isoformat(),
            sources=[s.source_name for s in sources],
            recordings={s.source_name: f"recordings/{s.source_name}/{session_id}.mp4" for s in sources},
            events=events
        )
        ManifestGenerator().save(manifest)
        print("Done. Manifest saved.")

def cmd_camera_test(args):
    cam = CameraCapture(0)
    cam.source_name = "camera"
    _record_loop([cam], args.duration)

def cmd_screen_test(args):
    scr = ScreenCapture(1)
    scr.source_name = "screen"
    _record_loop([scr], args.duration)

def cmd_record_both(args):
    cam = CameraCapture(0)
    cam.source_name = "camera"
    scr = ScreenCapture(1)
    scr.source_name = "screen"
    _record_loop([cam, scr], args.duration)

def main():
    parser = argparse.ArgumentParser(description="GyanDrishti Video Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    p_dev = subparsers.add_parser("devices", help="List devices")
    
    p_cam = subparsers.add_parser("camera-test", help="Test camera")
    p_cam.add_argument("--duration", type=int, default=10)
    
    p_scr = subparsers.add_parser("screen-test", help="Test screen")
    p_scr.add_argument("--duration", type=int, default=10)
    
    p_both = subparsers.add_parser("record-both", help="Record both")
    p_both.add_argument("--duration", type=int, default=10)
    
    args = parser.parse_args()
    
    if args.command == "devices":
        cmd_devices(args)
    elif args.command == "camera-test":
        cmd_camera_test(args)
    elif args.command == "screen-test":
        cmd_screen_test(args)
    elif args.command == "record-both":
        cmd_record_both(args)

if __name__ == "__main__":
    main()
