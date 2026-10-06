"""Keyframe extraction and storage module for GyanDrishti Video Engine."""

import os
from typing import Any, Dict
import cv2
import numpy as np

from ..schemas import Event


class KeyframeExtractor:
    """Extracts and persists keyframes when significant visual changes are flagged."""

    def __init__(self, output_dir: str = "backend/video_engine/output_frames") -> None:
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def save_keyframe(
        self,
        frame: np.ndarray,
        meta: Dict[str, Any],
        score: float,
        reason: str = "visual_change",
    ) -> Event:
        """Saves keyframe to local storage and returns an Event record."""
        source = meta.get("source", "unknown")
        ts = meta.get("timestamp", 0.0)
        frame_id = meta.get("frame_id", 0)

        filename = f"{source}_f{frame_id}_{int(ts * 1000)}.jpg"
        filepath = os.path.join(self.output_dir, filename)
        cv2.imwrite(filepath, frame)

        return Event(
            timestamp=float(ts),
            source=str(source),
            type="keyframe",
            change_score=round(float(score), 4),
            frame_path=filepath,
            reason=reason,
        )
