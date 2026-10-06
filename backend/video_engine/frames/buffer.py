from collections import deque
import time

class RollingBuffer:
    def __init__(self, duration_sec=30.0):
        self.duration_sec = duration_sec
        self.buffer = deque()
        
    def append(self, frame, metadata):
        self.buffer.append((frame, metadata))
        self._evict_old()
        
    def _evict_old(self):
        if not self.buffer: return
        now = time.time()
        while self.buffer and (now - self.buffer[0][1]['timestamp'] > self.duration_sec):
            self.buffer.popleft()
            
    def get_all(self):
        return list(self.buffer)
