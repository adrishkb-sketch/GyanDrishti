import cv2
import numpy as np

def detect_change(frame1, frame2, threshold=0.1):
    """
    Very basic change detection using absolute difference.
    Returns a score between 0 and 1 representing the change.
    """
    if frame1 is None or frame2 is None:
        return 0.0
    if frame1.shape != frame2.shape:
        frame2 = cv2.resize(frame2, (frame1.shape[1], frame1.shape[0]))
    
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    
    diff = cv2.absdiff(gray1, gray2)
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    
    change_score = np.sum(thresh > 0) / (thresh.shape[0] * thresh.shape[1])
    return float(change_score)
