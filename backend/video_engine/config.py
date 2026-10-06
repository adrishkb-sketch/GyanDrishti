from pydantic import BaseModel

class VideoConfig(BaseModel):
    storage_dir: str = "backend/video_engine"
    camera_fps: int = 30
    screen_fps: int = 30
    sample_fps: float = 2.0
    buffer_duration_sec: int = 30
    change_threshold: float = 0.8
    resolution: tuple[int, int] = (1280, 720)
