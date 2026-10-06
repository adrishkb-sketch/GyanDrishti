"""Frame sampling module for GyanDrishti Video Engine."""

from typing import Optional


class FrameSampler:
    """Controls frame extraction frequency based on target sampling FPS."""

    def __init__(self, target_fps: float = 2.0) -> None:
        self.target_fps = float(target_fps)
        self.interval = 1.0 / self.target_fps if self.target_fps > 0 else 0.5
        self.last_sampled_timestamp: Optional[float] = None

    def should_sample(self, timestamp: float) -> bool:
        """Determines whether a frame at the given timestamp should be sampled."""
        if self.last_sampled_timestamp is None:
            self.last_sampled_timestamp = timestamp
            return True
        if (timestamp - self.last_sampled_timestamp) >= (self.interval - 1e-6):
            self.last_sampled_timestamp = timestamp
            return True
        return False

    def reset(self) -> None:
        """Resets the sampling state."""
        self.last_sampled_timestamp = None
