"""GyanDrishti Local Semantic Retrieval and Memory RAG Engine.

Provides semantic chunking, local offline embeddings, vector indexing,
and evidence-grounded retrieval over Lecture Memory.
"""

from .schemas import (
    ChunkType,
    MemoryChunk,
    RetrievalResult,
    RetrievalFilter,
)
from .chunker import LectureMemoryChunker
from .embeddings import BaseEmbeddingModel, LocalDenseEmbeddingModel
from .index import LocalVectorIndex
from .retriever import SemanticLectureRetriever

__all__ = [
    "ChunkType",
    "MemoryChunk",
    "RetrievalResult",
    "RetrievalFilter",
    "LectureMemoryChunker",
    "BaseEmbeddingModel",
    "LocalDenseEmbeddingModel",
    "LocalVectorIndex",
    "SemanticLectureRetriever",
]
