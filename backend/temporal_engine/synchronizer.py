"""Temporal Synchronizer for GyanDrishti.

Associates speech segments and visual events into unified multimodal clusters
based on configurable temporal proximity windows (default: ±5 seconds).
Preserves raw source transcripts and visual event data without modification.
"""

from __future__ import annotations

from typing import List, Optional

from .schemas import (
    SpeechEvent,
    SynchronizedEvent,
    TemporalWindowConfig,
    VisualEvent,
)


class TemporalSynchronizer:
    """Synchronizes speech segments and visual events within configurable temporal windows."""

    def __init__(
        self,
        config: Optional[TemporalWindowConfig] = None,
        window_before: Optional[float] = None,
        window_after: Optional[float] = None,
    ) -> None:
        """Args:

        config: Optional TemporalWindowConfig instance.
        window_before: Optional override for seconds before speech (default: 5.0).
        window_after: Optional override for seconds after speech (default: 5.0).
        """
        self.config = config or TemporalWindowConfig()
        if window_before is not None:
            self.config.window_before = float(window_before)
        if window_after is not None:
            self.config.window_after = float(window_after)

    def synchronize(
        self,
        speech_events: List[SpeechEvent],
        visual_events: List[VisualEvent],
    ) -> List[SynchronizedEvent]:
        """Aligns speech events and visual events into a chronological list of SynchronizedEvents.

        Algorithm:
        1. Clusters consecutive speech segments separated by less than cluster_speech_gap (default 2.0s).
        2. For each speech cluster, defines temporal association boundary:
           [cluster.start - window_before, cluster.end + window_after].
        3. Assigns all visual events whose timestamps fall within this window to the cluster.
        4. Identifies visual events not associated with any speech (e.g. silent board writing)
           and creates visual-only synchronized blocks.
        5. Handles speech-only blocks (speech segments with no visual events in window).
        6. Deterministically orders all blocks by start timestamp.

        Returns:
            Deterministic list of SynchronizedEvent instances.
        """
        # Ensure inputs are sorted
        sorted_speech = sorted(speech_events, key=lambda s: (s.start, s.end, s.text))
        sorted_visual = sorted(visual_events, key=lambda v: (v.timestamp, v.source, v.frame_path))

        # Case 1: Both empty
        if not sorted_speech and not sorted_visual:
            return []

        # Case 2: No speech, only visual events
        if not sorted_speech:
            return self._build_visual_only_blocks(sorted_visual)

        # Case 3: Cluster speech segments
        speech_clusters: List[List[SpeechEvent]] = []
        curr_cluster: List[SpeechEvent] = [sorted_speech[0]]

        for seg in sorted_speech[1:]:
            prev_seg = curr_cluster[-1]
            gap = seg.start - prev_seg.end
            if gap <= self.config.cluster_speech_gap:
                curr_cluster.append(seg)
            else:
                speech_clusters.append(curr_cluster)
                curr_cluster = [seg]
        speech_clusters.append(curr_cluster)

        # Track which visual events were associated
        associated_visual_indices = set()
        synchronized_blocks: List[SynchronizedEvent] = []

        for cluster in speech_clusters:
            cluster_start = cluster[0].start
            cluster_end = cluster[-1].end

            win_start = cluster_start - self.config.window_before
            win_end = cluster_end + self.config.window_after

            # Find matching visual events in window
            matched_visuals: List[VisualEvent] = []
            for idx, ve in enumerate(sorted_visual):
                if win_start <= ve.timestamp <= win_end:
                    matched_visuals.append(ve)
                    associated_visual_indices.add(idx)

            # Block boundaries span the speech boundaries
            synchronized_blocks.append(
                SynchronizedEvent(
                    start=cluster_start,
                    end=cluster_end,
                    speech=cluster,
                    visual_events=matched_visuals,
                )
            )

        # Case 4: Unassociated visual events (silent board writing or gestures outside window)
        unassociated_visuals = [
            ve for idx, ve in enumerate(sorted_visual)
            if idx not in associated_visual_indices
        ]

        if unassociated_visuals:
            standalone_blocks = self._build_visual_only_blocks(unassociated_visuals)
            synchronized_blocks.extend(standalone_blocks)

        # Deterministic sort by start timestamp, then end timestamp
        return sorted(synchronized_blocks, key=lambda b: (b.start, b.end))

    def _build_visual_only_blocks(
        self,
        visual_events: List[VisualEvent],
    ) -> List[SynchronizedEvent]:
        """Groups visual events occurring outside speech into discrete synchronized blocks."""
        if not visual_events:
            return []

        blocks: List[SynchronizedEvent] = []
        curr_group: List[VisualEvent] = [visual_events[0]]

        for ve in visual_events[1:]:
            prev_ve = curr_group[-1]
            # If visual events are close together (<= 2.0s), group them
            if (ve.timestamp - prev_ve.timestamp) <= 2.0:
                curr_group.append(ve)
            else:
                blocks.append(
                    SynchronizedEvent(
                        start=curr_group[0].timestamp,
                        end=curr_group[-1].timestamp,
                        speech=[],
                        visual_events=curr_group,
                    )
                )
                curr_group = [ve]

        blocks.append(
            SynchronizedEvent(
                start=curr_group[0].timestamp,
                end=curr_group[-1].timestamp,
                speech=[],
                visual_events=curr_group,
            )
        )
        return blocks
