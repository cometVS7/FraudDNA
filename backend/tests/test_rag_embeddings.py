"""Unit tests for RAG embedding provider abstraction."""

import pytest

from app.rag.embeddings import (
    DeterministicLocalEmbeddingProvider,
    EmbeddingProviderError,
    ExternalAPIEmbeddingProvider,
    get_embedding_provider,
)


def test_local_provider_dimension_and_norm() -> None:
    provider = DeterministicLocalEmbeddingProvider(dimension=384)
    assert provider.dimension == 384

    text = "Coordinated device ring multi-account collusion"
    vec = provider.embed_text(text)

    assert len(vec) == 384
    # Check that vector is normalized (magnitude approx 1.0)
    import numpy as np

    norm = float(np.linalg.norm(vec))
    assert abs(norm - 1.0) < 1e-3


def test_local_provider_determinism() -> None:
    provider = DeterministicLocalEmbeddingProvider(dimension=384)
    text = "Suspicious proxy farm rotating residential IP addresses"

    vec1 = provider.embed_text(text)
    vec2 = provider.embed_text(text)

    assert vec1 == vec2


def test_local_provider_batch() -> None:
    provider = DeterministicLocalEmbeddingProvider(dimension=384)
    texts = ["Policy 1", "Policy 2", "Historical Case 3"]

    vectors = provider.embed_batch(texts)
    assert len(vectors) == 3
    for v in vectors:
        assert len(v) == 384


def test_local_provider_empty_text() -> None:
    provider = DeterministicLocalEmbeddingProvider(dimension=384)
    vec = provider.embed_text("")
    assert vec == [0.0] * 384


def test_external_provider_missing_key_raises_error() -> None:
    provider = ExternalAPIEmbeddingProvider(api_key=None)
    with pytest.raises(EmbeddingProviderError) as exc_info:
        provider.embed_text("test")

    assert "API key not configured" in str(exc_info.value)


def test_get_embedding_provider_factory() -> None:
    provider = get_embedding_provider()
    assert isinstance(provider, DeterministicLocalEmbeddingProvider)
