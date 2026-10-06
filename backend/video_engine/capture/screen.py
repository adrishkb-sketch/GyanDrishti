import mss
import numpy as np
import time
from .base import BaseCapture

class ScreenCapture(BaseCapture):
    def __init__(self, monitor_idx=1):
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[monitor_idx]
        self.frame_id = 0
        
    def read_frame(self):
        sct_img = self.sct.grab(self.monitor)
        frame = np.array(sct_img)
        # Convert BGRA to BGR
        frame = frame[:, :, :3]
        self.frame_id += 1
        return frame, {
            "source": "screen",
            "frame_id": self.frame_id,
            "timestamp": time.time(),
            "width": self.monitor["width"],
            "height": self.monitor["height"]
        }
    
    def release(self):
        self.sct.close()

def list_displays():
    with mss.mss() as sct:
        return sct.monitors[1:]
