import asyncio
import logging
import os
import re
import shutil
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
from lecture_memory.schemas import LectureMemory
from retrieval.retriever import SemanticLectureRetriever
from retrieval.schemas import RetrievalFilter
from understanding_engine.analyzer import LectureUnderstandingEngine
from understanding_engine.llm import OllamaProvider, MockLLMProvider
from video_processor import process_uploaded_lecture_video

logger = logging.getLogger("gyandrishti.api")

app = FastAPI(title="GyanDrishti API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure keyframes and upload directories exist and mount static route
if Path("video_engine").exists():
    keyframes_dir = Path("video_engine/recordings/keyframes")
    uploads_dir = Path("video_engine/recordings/uploads")
elif Path("backend/video_engine").exists():
    keyframes_dir = Path("backend/video_engine/recordings/keyframes")
    uploads_dir = Path("backend/video_engine/recordings/uploads")
else:
    keyframes_dir = Path("video_engine/recordings/keyframes")
    uploads_dir = Path("video_engine/recordings/uploads")

keyframes_dir.mkdir(parents=True, exist_ok=True)
uploads_dir.mkdir(parents=True, exist_ok=True)

app.mount("/api/video/keyframes", StaticFiles(directory=str(keyframes_dir)), name="keyframes")


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

@app.post("/api/lectures")
def save_lecture_memory(data: Dict[str, Any]):
    """Persists a new lecture memory and updates the local semantic retrieval index."""
    try:
        memory = LectureMemory.model_validate(data) if hasattr(LectureMemory, "model_validate") else LectureMemory.parse_obj(data)
        memory_storage.save(memory)
        try:
            retriever.index_lecture(memory)
        except Exception:
            pass
        return {"status": "saved", "session_id": memory.session_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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

# Semantic Memory Retrieval Endpoint
retriever = SemanticLectureRetriever()

@app.get("/api/search")
def search_lectures(q: str, top_k: int = 5, session_id: Optional[str] = None):
    """Searches across indexed lecture memories with cosine semantic similarity."""
    for meta in memory_storage.list_lectures():
        s_id = meta.get("session_id")
        if s_id and s_id not in retriever.index.session_index_map:
            try:
                mem = memory_storage.load(s_id)
                retriever.index_lecture(mem)
            except Exception:
                pass

    filter_crit = RetrievalFilter(session_id=session_id) if session_id else None
    results = retriever.search(q, top_k=top_k, filter_criteria=filter_crit)
    return {
        "query": q,
        "results": [
            {
                "score": r.score,
                "lecture_id": r.chunk.lecture_id,
                "session_id": r.chunk.session_id,
                "chunk_type": r.chunk.chunk_type.value,
                "timestamp_start": r.chunk.timestamp_start,
                "timestamp_end": r.chunk.timestamp_end,
                "source_type": r.chunk.source_type,
                "grounding_status": r.chunk.grounding_status,
                "text": r.chunk.text,
            }
            for r in results
        ],
    }

# Local LLM Notes Synthesis (Meta Llama 3.2 3B via Ollama)
ollama_provider = OllamaProvider(model="llama3.2:3b")
notes_engine = LectureUnderstandingEngine(
    provider=ollama_provider if ollama_provider.is_available() else MockLLMProvider()
)

class GenerateNotesRequest(BaseModel):
    session_id: Optional[str] = None
    title: Optional[str] = "Classroom Lecture"
    transcript_lines: List[Dict[str, Any]] = []
    visual_events: List[Dict[str, Any]] = []

@app.get("/api/notes/status")
def get_notes_model_status():
    """Returns local LLM provider status and model metadata."""
    is_avail = ollama_provider.is_available()
    return {
        "status": "ready" if is_avail else "fallback_ready",
        "provider": "ollama" if is_avail else "mock",
        "model": "llama3.2:3b" if is_avail else "mock_pedagogical_llm",
        "model_label": "Meta Llama 3.2 (3B Parameters • Open-Source)",
        "hardware": "Apple Silicon (GPU/Metal Acceleration)" if is_avail else "CPU Fallback",
        "is_local": True
    }

@app.post("/api/notes/generate")
def generate_ai_notes(req: GenerateNotesRequest):
    """Synthesizes structured pedagogical notes using local open-source Llama 3.2."""
    try:
        # Prepare speech segments format
        speech_segs = []
        for idx, line in enumerate(req.transcript_lines):
            speech_segs.append({
                "id": idx + 1,
                "start": float(idx * 5.0),
                "end": float((idx + 1) * 5.0),
                "text": line.get("text", "")
            })
        if not speech_segs:
            speech_segs.append({
                "id": 1,
                "start": 0.0,
                "end": 30.0,
                "text": "Introduction to electrical circuits, Ohm's law relation, and power formula."
            })

        understanding = notes_engine.analyze_block(
            start_time=0.0,
            end_time=max(30.0, float(len(speech_segs) * 5.0)),
            speech_segments=speech_segs,
            visual_events=req.visual_events,
            lecture_id=req.session_id or f"session_{int(time.time())}"
        )

        return {
            "status": "success",
            "model_name": understanding.model_name or "ollama/llama3.2:3b",
            "topic": understanding.topic,
            "concepts": [c.model_dump() if hasattr(c, "model_dump") else c.dict() for c in understanding.concepts],
            "definitions": [d.model_dump() if hasattr(d, "model_dump") else d.dict() for d in understanding.definitions],
            "equations": [e.model_dump() if hasattr(e, "model_dump") else e.dict() for e in understanding.equations],
            "important_points": [p.model_dump() if hasattr(p, "model_dump") else p.dict() for p in understanding.important_points],
            "question_candidates": [q.model_dump() if hasattr(q, "model_dump") else q.dict() for q in understanding.question_candidates],
            "grounding_score": understanding.grounding_score,
            "confidence": understanding.confidence
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate notes: {str(e)}")


@app.post("/api/video/upload")
async def upload_lecture_video(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    subject: Optional[str] = Form("Classroom Lecture"),
    gemini_api_keys: Optional[str] = Form(None),
):
    """Processes an uploaded video file:
    1. Extracts audio & runs multilingual Whisper transcription (EN, HI, BN).
    2. Runs frame-by-frame chalkboard change detection & RapidOCR equation/text recognition.
    3. Fuses speech + visual events with Gemini Vision & Multimodal temporal alignment.
    4. Cooperatively synthesizes notes and revision questions with Gemini + Llama 3.2.
    5. Saves canonical LectureMemory with visual diagrams & indexes into vector retriever.
    """
    try:
        session_id = f"upload_{int(time.time())}"
        ext = Path(file.filename or "uploaded.mp4").suffix or ".mp4"
        saved_video_path = uploads_dir / f"{session_id}{ext}"

        with open(saved_video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        lecture_title = title.strip() if title and title.strip() else (file.filename or "Recorded Lecture").rsplit(".", 1)[0]

        parsed_gemini_keys = None
        if gemini_api_keys:
            raw_keys = [k.strip() for k in re.split(r'[,;\n\r\s]+', gemini_api_keys) if k.strip()]
            if raw_keys:
                parsed_gemini_keys = raw_keys
                logger.info(f"Received {len(parsed_gemini_keys)} Gemini API key(s) for upload session {session_id}")

        result = await asyncio.to_thread(
            process_uploaded_lecture_video,
            video_path=saved_video_path,
            title=lecture_title,
            session_id=session_id,
            subject=subject or "Classroom Lecture",
            gemini_api_keys=parsed_gemini_keys
        )
        return result
    except Exception as e:
        logger.exception(f"Upload processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process video: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

