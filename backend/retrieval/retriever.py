"""High-level semantic retriever for searching across lecture memories."""

import time
from typing import Dict, List, Optional
from lecture_memory.schemas import LectureMemory
from .chunker import LectureMemoryChunker
from .embeddings import BaseEmbeddingModel, LocalDenseEmbeddingModel
from .index import LocalVectorIndex
from .schemas import (
    MemoryChunk,
    RetrievalFilter,
    RetrievalResult,
)


class SemanticLectureRetriever:
    """Manages indexing, embedding, and semantic search over completed lectures."""

    def __init__(
        self,
        embedding_model: Optional[BaseEmbeddingModel] = None,
        index: Optional[LocalVectorIndex] = None,
    ) -> None:
        self.embedding_model = embedding_model or LocalDenseEmbeddingModel()
        self.index = index or LocalVectorIndex()

    def index_lecture(self, memory: LectureMemory) -> Dict[str, float]:
        """Extracts chunks from LectureMemory, generates embeddings, and adds to index."""
        t0 = time.perf_counter()
        chunks = LectureMemoryChunker.chunk_lecture(memory)
        chunking_ms = (time.perf_counter() - t0) * 1000.0

        t1 = time.perf_counter()
        texts = [c.text for c in chunks]
        embeddings = self.embedding_model.embed_batch(texts)
        embedding_ms = (time.perf_counter() - t1) * 1000.0

        t2 = time.perf_counter()
        self.index.add_lecture_chunks(memory.session_id, chunks, embeddings)
        indexing_ms = (time.perf_counter() - t2) * 1000.0

        return {
            "chunks_count": float(len(chunks)),
            "chunking_ms": round(chunking_ms, 2),
            "embedding_ms": round(embedding_ms, 2),
            "indexing_ms": round(indexing_ms, 2),
            "total_ms": round(chunking_ms + embedding_ms + indexing_ms, 2),
        }

    def remove_lecture(self, session_id: str) -> bool:
        """Removes a lecture from the search index."""
        return self.index.remove_lecture(session_id)

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_criteria: Optional[RetrievalFilter] = None,
    ) -> List[RetrievalResult]:
        """Embeds natural language query and retrieves top-k semantically relevant chunks."""
        q_vec = self.embedding_model.embed_text(query)
        return self.index.search(
            query_vector=q_vec,
            top_k=top_k,
            filter_criteria=filter_criteria,
        )
