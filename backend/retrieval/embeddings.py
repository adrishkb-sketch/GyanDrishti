"""Local, offline embedding models for GyanDrishti semantic memory retrieval.

Provides deterministic, zero-network vector representations without cloud APIs.
"""

from abc import ABC, abstractmethod
import hashlib
import re
from typing import List
import numpy as np


class BaseEmbeddingModel(ABC):
    """Abstract interface for local embedding engines."""

    @abstractmethod
    def embed_text(self, text: str) -> np.ndarray:
        """Returns 1D float32 normalized embedding vector."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Returns 2D float32 normalized embedding matrix [N, D]."""
        pass


class LocalDenseEmbeddingModel(BaseEmbeddingModel):
    """Deterministic, lightweight dense semantic embedding model.

    Projects token unigrams, bigrams, and character n-grams into a normalized
    128-dimensional latent space using locality-sensitive hashed projection.
    Semantically overlapping queries and chunks yield high cosine similarities,
    while orthogonal/irrelevant topics yield near-zero similarity.
    100% offline with zero external downloads.
    """

    def __init__(self, dimension: int = 128) -> None:
        self.dimension = dimension

    def _tokenize(self, text: str) -> List[str]:
        # Unicode-friendly tokenization: words and numbers
        words = re.findall(r"\b\w+\b", text.lower())
        tokens = list(words)
        # Add bigrams for phrase matching (e.g. "ohm's law", "electric current")
        for i in range(len(words) - 1):
            tokens.append(f"{words[i]}_{words[i+1]}")
        # Add subword 3-character n-grams for root matching
        for w in words:
            if len(w) >= 4:
                for j in range(len(w) - 2):
                    tokens.append(w[j : j + 3])
        return tokens

    def _hash_token_to_vector(self, token: str) -> np.ndarray:
        # Deterministic pseudo-random vector from MD5 digest
        digest = hashlib.md5(token.encode("utf-8")).digest()
        # Seed deterministic generator with digest
        seed = int.from_bytes(digest[:4], "little")
        rng = np.random.RandomState(seed)
        vec = rng.randn(self.dimension).astype(np.float32)
        return vec

    def embed_text(self, text: str) -> np.ndarray:
        """Embeds single string into a unit-normalized float32 vector."""
        tokens = self._tokenize(text)
        if not tokens:
            vec = np.zeros(self.dimension, dtype=np.float32)
            vec[0] = 1.0
            return vec

        accum = np.zeros(self.dimension, dtype=np.float32)
        for token in tokens:
            t_vec = self._hash_token_to_vector(token)
            accum += t_vec

        norm = np.linalg.norm(accum)
        if norm > 1e-8:
            accum /= norm
        else:
            accum[0] = 1.0
        return accum

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Embeds multiple texts into a [N, D] matrix."""
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)
        vectors = [self.embed_text(t) for t in texts]
        return np.vstack(vectors)
