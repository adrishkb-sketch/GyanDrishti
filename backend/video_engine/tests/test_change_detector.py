import pytest
import numpy as np
from backend.video_engine.frames.change_detector import ChangeDetector

def test_change_detector():
    detector = ChangeDetector(threshold=0.1)
    frame1 = np.zeros((100, 100, 3), dtype=np.uint8)
    frame2 = np.ones((100, 100, 3), dtype=np.uint8) * 255
    
    score, changed = detector.check_change(frame1)
    assert not changed
    
    score, changed = detector.check_change(frame2)
    assert changed
    assert score > 0.1
