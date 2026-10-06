"""Visual change detector for classroom board and presentation dynamics."""

from typing import Optional, Tuple
import numpy as np

from ..detection.motion import detect_change


class ChangeDetector:
    """Compares consecutive frames using pixel difference to flag visual events."""

    def __init__(self, threshold: float = 0.1) -> None:
        self.threshold = threshold
        self.prev_frame: Optional[np.ndarray] = None

    def check_change(self, frame: np.ndarray) -> Tuple[float, bool]:
        """Compares incoming frame with previous frame.

        Returns:
            Tuple of (change_score: float, is_changed: bool).
            First frame always returns (0.0, False).
        """
        if self.prev_frame is None:
            self.prev_frame = frame.copy()
            return 0.0, False

        score = detect_change(self.prev_frame, frame, threshold=self.threshold)
        is_changed = bool(score > self.threshold)
        self.prev_frame = frame.copy()
        return score, is_changed

    def reset(self) -> None:
        """Resets the reference frame."""
        self.prev_frame = None
