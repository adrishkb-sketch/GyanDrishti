"""Unit tests for TemporalSynchronizer in Temporal Engine."""

import pytest
from temporal_engine.schemas import (
    SpeechEvent,
    TemporalWindowConfig,
    VisualEvent,
)
from temporal_engine.synchronizer import TemporalSynchronizer


def test_exact_timestamp_match() -> None:
    sync = TemporalSynchronizer(window_before=5.0, window_after=5.0)
    speech = [SpeechEvent(start=10.0, end=14.0, text="Deriving EMF equation")]
    visual = [VisualEvent(timestamp=10.0, source="camera", frame_path="/tmp/f1.jpg")]

    blocks = sync.synchronize(speech, visual)
    assert len(blocks) == 1
    assert blocks[0].start == 10.0
    assert blocks[0].end == 14.0
    assert len(blocks[0].speech) == 1
    assert len(blocks[0].visual_events) == 1
    assert blocks[0].visual_events[0].timestamp == 10.0


def test_visual_event_one_second_before_speech() -> None:
    sync = TemporalSynchronizer(window_before=5.0, window_after=5.0)
    # Speech starts at 10.0, visual event at 9.0 (1.0s before start)
    speech = [SpeechEvent(start=10.0, end=15.0, text="Look at the screen")]
    visual = [VisualEvent(timestamp=9.0, source="screen", frame_path="/tmp/slide1.jpg")]

    blocks = sync.synchronize(speech, visual)
    assert len(blocks) == 1
    assert len(blocks[0].visual_events) == 1
    assert blocks[0].visual_events[0].timestamp == 9.0


def test_visual_event_one_second_after_speech() -> None:
    sync = TemporalSynchronizer(window_before=5.0, window_after=5.0)
    # Speech ends at 15.0, visual event at 16.0 (1.0s after end)
    speech = [SpeechEvent(start=10.0, end=15.0, text="Look at the board")]
    visual = [VisualEvent(timestamp=16.0, source="camera", frame_path="/tmp/board1.jpg")]

    blocks = sync.synchronize(speech, visual)
    assert len(blocks) == 1
    assert len(blocks[0].visual_events) == 1
    assert blocks[0].visual_events[0].timestamp == 16.0


def test_multiple_visual_events_around_one_speech_segment() -> None:
    sync = TemporalSynchronizer(window_before=5.0, window_after=5.0)
    speech = [SpeechEvent(start=10.0, end=15.0, text="Explaining induction")]
    visual = [
        VisualEvent(timestamp=7.0, source="camera", frame_path="/tmp/v1.jpg"),   # 3s before
        VisualEvent(timestamp=12.0, source="screen", frame_path="/tmp/v2.jpg"),  # during
        VisualEvent(timestamp=18.0, source="camera", frame_path="/tmp/v3.jpg"),  # 3s after
    ]

    blocks = sync.synchronize(speech, visual)
    assert len(blocks) == 1
    assert len(blocks[0].visual_events) == 3
    assert [v.timestamp for v in blocks[0].visual_events] == [7.0, 12.0, 18.0]


def test_multiple_speech_segments_around_one_visual_event() -> None:
    sync = TemporalSynchronizer(
        config=TemporalWindowConfig(window_before=5.0, window_after=5.0, cluster_speech_gap=1.5)
    )
    # Two speech segments separated by 1.0s (clustered into one pedagogical block [10.0, 17.0])
    speech = [
        SpeechEvent(start=10.0, end=13.0, text="First part"),
        SpeechEvent(start=14.0, end=17.0, text="Second part"),
    ]
    visual = [VisualEvent(timestamp=13.5, source="screen", frame_path="/tmp/slide.jpg")]

    blocks = sync.synchronize(speech, visual)
    assert len(blocks) == 1
    assert len(blocks[0].speech) == 2
    assert len(blocks[0].visual_events) == 1
    assert blocks[0].visual_events[0].timestamp == 13.5


def test_events_outside_window_not_associated() -> None:
    # Window is ±5.0 seconds
    sync = TemporalSynchronizer(window_before=5.0, window_after=5.0)
    speech = [SpeechEvent(start=20.0, end=25.0, text="Faraday's Law")]
    visual = [
        VisualEvent(timestamp=12.0, source="camera", frame_path="/tmp/too_early.jpg"),  # 8s before
        VisualEvent(timestamp=32.0, source="camera", frame_path="/tmp/too_late.jpg"),   # 7s after
    ]

    blocks = sync.synchronize(speech, visual)
    # The speech block has 0 associated visual events
    speech_block = [b for b in blocks if len(b.speech) > 0][0]
    assert len(speech_block.visual_events) == 0

    # Unassociated visual events form their own standalone blocks
    visual_blocks = [b for b in blocks if len(b.speech) == 0]
    assert len(visual_blocks) == 2
    assert visual_blocks[0].visual_events[0].timestamp == 12.0
    assert visual_blocks[1].visual_events[0].timestamp == 32.0


def test_empty_speech_input() -> None:
    sync = TemporalSynchronizer()
    visual = [VisualEvent(timestamp=5.0, source="camera", frame_path="/tmp/silent_board.jpg")]
    blocks = sync.synchronize([], visual)
    assert len(blocks) == 1
    assert len(blocks[0].speech) == 0
    assert len(blocks[0].visual_events) == 1
    assert blocks[0].visual_events[0].timestamp == 5.0


def test_empty_visual_input() -> None:
    sync = TemporalSynchronizer()
    speech = [SpeechEvent(start=1.0, end=4.0, text="Only audio lecture")]
    blocks = sync.synchronize(speech, [])
    assert len(blocks) == 1
    assert len(blocks[0].speech) == 1
    assert len(blocks[0].visual_events) == 0


def test_mixed_camera_and_screen_events() -> None:
    sync = TemporalSynchronizer(window_before=5.0, window_after=5.0)
    speech = [SpeechEvent(start=10.0, end=20.0, text="Mixed presentation")]
    visual = [
        VisualEvent(timestamp=11.0, source="screen", frame_path="/tmp/s1.jpg"),
        VisualEvent(timestamp=12.0, source="camera", frame_path="/tmp/c1.jpg"),
    ]

    blocks = sync.synchronize(speech, visual)
    assert len(blocks) == 1
    sources = [v.source for v in blocks[0].visual_events]
    assert "screen" in sources
    assert "camera" in sources


def test_duplicate_timestamps_handled_cleanly() -> None:
    sync = TemporalSynchronizer(window_before=5.0, window_after=5.0)
    speech = [SpeechEvent(start=10.0, end=15.0, text="Speech at 10.0")]
    visual = [
        VisualEvent(timestamp=10.0, source="camera", frame_path="/tmp/c.jpg"),
        VisualEvent(timestamp=10.0, source="screen", frame_path="/tmp/s.jpg"),
    ]

    blocks = sync.synchronize(speech, visual)
    assert len(blocks) == 1
    assert len(blocks[0].visual_events) == 2
