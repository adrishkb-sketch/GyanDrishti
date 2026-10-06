import asyncio
import threading
import time
from datetime import datetime
from typing import List, Optional, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from video_engine.capture.camera import CameraCapture, list_cameras
from video_engine.capture.screen import ScreenCapture, list_displays
from video_engine.storage.video_writer import LocalVideoWriter
from video_engine.frames.sampler import FrameSampler
from video_engine.frames.change_detector import ChangeDetector
from video_engine.frames.keyframes import KeyframeExtractor
from video_engine.storage.manifest import ManifestGenerator
from video_engine.schemas import Manifest
from lecture_memory.storage import (
    LectureMemoryStorage,
    MemoryNotFoundError,
    CorruptMemoryError,
    InvalidSessionIdError,
)

app = FastAPI(title="GyanDrishti API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SessionManager:
    def __init__(self):
        self.session_id: Optional[str] = None
        self.is_recording = False
        self.is_paused = False
        self.sources = []
        self.writers = {}
        self.detectors = {}
        self.extractor = None
        self.sampler = None
        self.events = []
        self.start_time = 0
        self.duration = 0
        self.thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start_session(self, camera_id: int, screen_id: int):
        if self.is_recording:
            raise Exception("Session already running")
            
        self.session_id = f"lecture_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.is_recording = True
        self.is_paused = False
        self._stop_event.clear()
        self.events = []
        
        try:
            self.sources = []
            if camera_id >= 0:
                cam = CameraCapture(camera_id)
                cam.source_name = "camera"
                self.sources.append(cam)
            if screen_id >= 0:
                scr = ScreenCapture(screen_id)
                scr.source_name = "screen"
                self.sources.append(scr)
                
            self.writers = {}
            for s in self.sources:
                out_path = f"video_engine/recordings/{s.source_name}/{self.session_id}.mp4"
                self.writers[s.source_name] = LocalVideoWriter(out_path, fps=10)
                
            self.sampler = FrameSampler(target_fps=2.0)
            self.detectors = {s.source_name: ChangeDetector(threshold=0.05) for s in self.sources}
            self.extractor = KeyframeExtractor()
            
            self.start_time = time.time()
            self.duration = 0
            
            self.thread = threading.Thread(target=self._record_loop)
            self.thread.start()
        except Exception as e:
            self.is_recording = False
            for s in self.sources:
                try: s.release()
                except: pass
            raise e

    def _record_loop(self):
        fps = 10
        try:
            while not self._stop_event.is_set():
                if self.is_paused:
                    time.sleep(0.1)
                    continue
                    
                now = time.time()
                for src in self.sources:
                    frame, meta = src.read_frame()
                    if frame is not None:
                        self.writers[src.source_name].write(frame)
                        
                        if self.sampler.should_sample(now):
                            score, is_changed = self.detectors[src.source_name].check_change(frame)
                            if is_changed:
                                evt = self.extractor.save_keyframe(frame, meta, score, "visual_change")
                                self.events.append(evt)
                
                self.duration += 1.0 / fps
                time.sleep(1.0 / fps)
        except Exception as e:
            print(f"Error in record loop: {e}")
        finally:
            for src in self.sources:
                src.release()
                self.writers[src.source_name].release()
                
            manifest = Manifest(
                session_id=self.session_id,
                start_time=datetime.fromtimestamp(self.start_time).isoformat(),
                sources=[s.source_name for s in self.sources],
                recordings={s.source_name: f"recordings/{s.source_name}/{self.session_id}.mp4" for s in self.sources},
                events=self.events
            )
            ManifestGenerator().save(manifest)
            self.is_recording = False

    def stop_session(self):
        if not self.is_recording:
            return
        self._stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
            
    def pause_session(self):
        if self.is_recording:
            self.is_paused = True
            
    def resume_session(self):
        if self.is_recording:
            self.is_paused = False

    def get_status(self):
        return {
            "session_id": self.session_id,
            "is_recording": self.is_recording,
            "is_paused": self.is_paused,
            "duration": int(self.duration),
            "events_count": len(self.events),
            "events": [evt.dict() if hasattr(evt, 'dict') else dict(evt) for evt in self.events]
        }

manager = SessionManager()

class StartSessionRequest(BaseModel):
    camera_id: int = 0
    screen_id: int = 1

@app.get("/api/video/devices")
def get_devices():
    cams = list_cameras()
    displays = list_displays()
    
    return {
        "cameras": [{"id": c, "name": f"Camera {c}"} for c in cams],
        "screens": [{"id": i+1, "name": f"Display {i+1} ({d['width']}x{d['height']})"} for i, d in enumerate(displays)]
    }

@app.post("/api/video/session/start")
def start_session(req: StartSessionRequest):
    try:
        manager.start_session(req.camera_id, req.screen_id)
        return {"session_id": manager.session_id, "status": "started"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/video/session/pause")
def pause_session():
    manager.pause_session()
    return {"status": "paused"}

@app.post("/api/video/session/resume")
def resume_session():
    manager.resume_session()
    return {"status": "resumed"}

@app.post("/api/video/session/stop")
def stop_session():
    manager.stop_session()
    return {"status": "stopped", "session_id": manager.session_id, "duration": manager.duration, "events_count": len(manager.events)}

@app.get("/api/video/session/status")
def session_status():
    return manager.get_status()

# Lecture Memory Endpoints
memory_storage = LectureMemoryStorage()

@app.get("/api/lectures")
def list_lectures():
    """Returns index of all locally persisted lecture memories."""
    return {"lectures": memory_storage.list_lectures()}

@app.get("/api/lectures/{session_id}")
def get_lecture_memory(session_id: str):
    """Retrieves full canonical lecture memory formatted for frontend viewer."""
    try:
        memory = memory_storage.load(session_id)
        return memory.to_frontend_dict()
    except MemoryNotFoundError:
        raise HTTPException(status_code=404, detail=f"Lecture memory '{session_id}' not found")
    except InvalidSessionIdError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CorruptMemoryError as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
