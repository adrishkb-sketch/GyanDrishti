"""Tests for local dense embedding model."""

import numpy as np
import pytest
from retrieval.embeddings import BaseEmbeddingModel, LocalDenseEmbeddingModel


def test_embedding_normalization():
    model = LocalDenseEmbeddingModel(dimension=128)
    vec = model.embed_text("Ohm's law relates current and voltage")
    norm = np.linalg.norm(vec)
    assert np.isclose(norm, 1.0, atol=1e-5)


def test_13_unicode_embeddings():
    """Requirement 13: Unicode queries and chunk texts work (English, Hindi, Bengali)."""
    model = LocalDenseEmbeddingModel(dimension=128)
    texts = [
        "Ohm's Law formula: I = V / R",
        "ओम का नियम: धारा = विभव / प्रतिरोध",
        "ওহমের সূত্র: তড়িৎ প্রবাহ = বিভব / রোধ",
    ]
    matrix = model.embed_batch(texts)
    assert matrix.shape == (3, 128)
    for i in range(3):
        assert np.isclose(np.linalg.norm(matrix[i]), 1.0, atol=1e-5)


def test_14_15_offline_execution_zero_cloud(monkeypatch):
    """Requirements 14 & 15: Offline execution without network or cloud APIs."""
    import socket

    def guarded_connect(*args, **kwargs):
        raise RuntimeError("Network attempted during offline embedding generation!")

    monkeypatch.setattr(socket, "socket", guarded_connect)

    model = LocalDenseEmbeddingModel()
    vec = model.embed_text("Testing completely local vector space")
    assert len(vec) == 128
    assert not hasattr(model, "openai_api_key")
    assert not hasattr(model, "supabase")
