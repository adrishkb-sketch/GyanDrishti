"""Local vector index for semantic lecture retrieval using numpy vector operations."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np

from .schemas import (
    MemoryChunk,
    RetrievalFilter,
    RetrievalResult,
)


class LocalVectorIndex:
    """Manages local in-memory and disk-persisted vector index with cosine search."""

    def __init__(self, dimension: int = 128) -> None:
        self.dimension = dimension
        self.chunks: List[MemoryChunk] = []
        self.embeddings: np.ndarray = np.empty((0, dimension), dtype=np.float32)
        # Session ID to chunk indices mapping
        self.session_index_map: Dict[str, List[str]] = {}

    def add_lecture_chunks(
        self,
        session_id: str,
        chunks: List[MemoryChunk],
        embeddings: np.ndarray,
    ) -> None:
        """Indexes chunks and embeddings for a lecture, replacing duplicates if existing."""
        if session_id in self.session_index_map:
            self.remove_lecture(session_id)

        if not chunks:
            self.session_index_map[session_id] = []
            return

        new_chunk_ids = [c.chunk_id for c in chunks]
        self.chunks.extend(chunks)

        if self.embeddings.shape[0] == 0:
            self.embeddings = embeddings.astype(np.float32)
        else:
            self.embeddings = np.vstack([self.embeddings, embeddings.astype(np.float32)])

        self.session_index_map[session_id] = new_chunk_ids

    def remove_lecture(self, session_id: str) -> bool:
        """Removes all indexed chunks associated with a session ID."""
        if session_id not in self.session_index_map:
            return False

        chunk_ids_to_remove = set(self.session_index_map[session_id])
        del self.session_index_map[session_id]

        keep_indices = [
            idx for idx, c in enumerate(self.chunks)
            if c.chunk_id not in chunk_ids_to_remove
        ]

        self.chunks = [self.chunks[i] for i in keep_indices]
        if keep_indices:
            self.embeddings = self.embeddings[keep_indices]
        else:
            self.embeddings = np.empty((0, self.dimension), dtype=np.float32)

        return True

    def rebuild_index(self) -> None:
        """Ensures internal index consistency and recalculates embeddings matrix."""
        # Clean up chunk list and verify consistency
        reconstructed_map: Dict[str, List[str]] = {}
        for c in self.chunks:
            if c.session_id not in reconstructed_map:
                reconstructed_map[c.session_id] = []
            reconstructed_map[c.session_id].append(c.chunk_id)
        self.session_index_map = reconstructed_map

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        filter_criteria: Optional[RetrievalFilter] = None,
    ) -> List[RetrievalResult]:
        """Performs cosine similarity search against indexed chunks."""
        if len(self.chunks) == 0 or self.embeddings.shape[0] == 0:
            return []

        # Cosine similarity: dot product of normalized query with normalized embeddings
        scores = np.dot(self.embeddings, query_vector.astype(np.float32))

        criteria = filter_criteria or RetrievalFilter()

        # Gather valid results
        candidates: List[RetrievalResult] = []
        for idx, score_val in enumerate(scores):
            chunk = self.chunks[idx]

            # Filter out untrusted if requested
            if criteria.only_trusted and chunk.grounding_status == "unsupported":
                continue

            # Filter by session_id
            if criteria.session_id and chunk.session_id != criteria.session_id:
                continue

            # Filter by chunk_type
            if criteria.chunk_type and chunk.chunk_type != criteria.chunk_type:
                continue

            # Filter by source_type
            if criteria.source_type and chunk.source_type != criteria.source_type:
                continue

            # Filter by min_score
            score_float = float(score_val)
            if score_float < criteria.min_score:
                continue

            candidates.append(
                RetrievalResult(
                    score=score_float,
                    chunk=chunk,
                )
            )

        # Sort descending by score
        candidates.sort(key=lambda r: r.score, reverse=True)
        return candidates[:top_k]

    def save_index(self, directory_path: str | Path) -> Path:
        """Saves chunks and embeddings to local directory."""
        dir_path = Path(directory_path)
        dir_path.mkdir(parents=True, exist_ok=True)

        chunks_data = [c.model_dump(mode="json") for c in self.chunks]
        with open(dir_path / "chunks.json", "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, indent=2, ensure_ascii=False)

        np.save(dir_path / "embeddings.npy", self.embeddings)

        with open(dir_path / "index_map.json", "w", encoding="utf-8") as f:
            json.dump(self.session_index_map, f, indent=2)

        return dir_path

    @classmethod
    def load_index(cls, directory_path: str | Path, dimension: int = 128) -> LocalVectorIndex:
        """Loads chunks and embeddings from local directory."""
        dir_path = Path(directory_path)
        index = cls(dimension=dimension)

        chunks_file = dir_path / "chunks.json"
        embeds_file = dir_path / "embeddings.npy"
        map_file = dir_path / "index_map.json"

        if not chunks_file.exists() or not embeds_file.exists():
            return index

        with open(chunks_file, "r", encoding="utf-8") as f:
            raw_chunks = json.load(f)
        index.chunks = [MemoryChunk.model_validate(c) for c in raw_chunks]

        index.embeddings = np.load(embeds_file).astype(np.float32)

        if map_file.exists():
            with open(map_file, "r", encoding="utf-8") as f:
                index.session_index_map = json.load(f)
        else:
            index.rebuild_index()

        return index
