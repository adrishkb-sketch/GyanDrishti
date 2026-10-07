import cv2
import time
from .base import BaseCapture

class CameraCapture(BaseCapture):
    def __init__(self, device_id=0):
        self.device_id = device_id
        self.cap = cv2.VideoCapture(device_id)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open camera {device_id}. Check permissions.")
        self.frame_id = 0
    
    def read_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None, None
        self.frame_id += 1
        return frame, {
            "source": "camera",
            "frame_id": self.frame_id,
            "timestamp": time.time(),
            "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        }
    
    def release(self):
        self.cap.release()

def list_cameras():
    cams = []
    # Test first 2 indices (primary camera and potential external)
    for i in range(2):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            cams.append(i)
            cap.release()
        else:
            break
    if not cams:
        # Fallback to index 0
        cams = [0]
    return cams
