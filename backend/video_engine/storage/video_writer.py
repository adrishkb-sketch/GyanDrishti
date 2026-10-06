import cv2
import os

class LocalVideoWriter:
    def __init__(self, output_path, fps=30, resolution=(1280, 720)):
        self.output_path = output_path
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(output_path, fourcc, fps, resolution)
        self.resolution = resolution
        
    def write(self, frame):
        if self.writer is not None:
            if frame.shape[:2] != (self.resolution[1], self.resolution[0]):
                frame = cv2.resize(frame, self.resolution)
            self.writer.write(frame)
            
    def release(self):
        if self.writer is not None:
            self.writer.release()
