"""FraudDNA Embedding Provider Abstraction.

Defines the pluggable embedding interface, deterministic local provider for offline/test
execution, and external API adapter for production embeddings.
"""

import hashlib
import os
import re
from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class EmbeddingProviderError(Exception):
    """Raised when an embedding provider fails to generate vector embeddings."""


class BaseEmbeddingProvider(ABC):
    """Abstract base class for RAG embedding generation."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the vector dimensionality of generated embeddings."""

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Generate vector embedding for a single text string."""

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings for a list of text strings."""
        return [self.embed_text(t) for t in texts]


class DeterministicLocalEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic local embedding provider for development, CI, and offline testing.

    Generates reproducible unit-normalized 384-dimensional dense vectors using character
    and token n-gram feature hashing. Preserves semantic clustering for overlapping fraud
    and policy terminology without external network dependencies.

    NOTE: This is a development/testing provider designed to avoid external paid API
    dependencies during test runs. It is NOT equivalent to production transformer
    embeddings (e.g. text-embedding-3-small or Voyage) which should be used in production.
    """

    def __init__(self, dimension: int = 384) -> None:
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_text(self, text: str) -> list[float]:
        """Generate a deterministic unit-normalized vector embedding."""
        if not text or not text.strip():
            # Return zero vector if text is empty
            return [0.0] * self._dimension

        vec = np.zeros(self._dimension, dtype=np.float64)

        # Normalize text to lower-case alphanumeric tokens
        clean_text = text.lower()
        tokens = re.findall(r"\b\w+\b", clean_text)

        # 1. Unigram & Bigram Feature Hashing
        features: list[str] = []
        for i, token in enumerate(tokens):
            features.append(f"w:{token}")
            if i > 0:
                features.append(f"bi:{tokens[i-1]}_{token}")

        # 2. Add 3-character subword n-grams for typo & morphological resilience
        for token in tokens:
            if len(token) >= 3:
                for j in range(len(token) - 2):
                    features.append(f"ch:{token[j:j+3]}")

        for feat in features:
            h = int(hashlib.md5(feat.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dimension
            sign = 1.0 if ((h >> 16) & 1) == 0 else -1.0
            vec[idx] += sign

        # Global document hash injection for unique tie-breaking
        doc_hash = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)
        for k in range(8):
            pos = (doc_hash >> (k * 8)) % self._dimension
            vec[pos] += 0.05

        # L2 Normalization so dot product == cosine similarity
        norm = float(np.linalg.norm(vec))
        if norm > 0.0:
            vec = vec / norm

        return [round(float(x), 6) for x in vec]


class ExternalAPIEmbeddingProvider(BaseEmbeddingProvider):
    """Production provider connecting to standard HTTP embedding endpoints (e.g. OpenAI / Voyage)."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "text-embedding-3-small",
        dimension: int = 1536,
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 10.0,
    ) -> None:
        self._api_key = api_key or os.getenv("EMBEDDING_API_KEY")
        self._model_name = model_name
        self._dimension = dimension
        self._base_url = base_url
        self._timeout = timeout

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_text(self, text: str) -> list[float]:
        if not self._api_key:
            raise EmbeddingProviderError(
                "Embedding API key not configured. Set EMBEDDING_API_KEY environment variable."
            )

        import httpx

        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(
                    f"{self._base_url}/embeddings",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json={"input": text, "model": self._model_name},
                )
                resp.raise_for_status()
                data: dict[str, Any] = resp.json()
                embedding = data["data"][0]["embedding"]
                return [float(x) for x in embedding]
        except Exception as e:
            raise EmbeddingProviderError(f"External embedding API failed: {e}") from e


def get_embedding_provider(provider_type: str | None = None) -> BaseEmbeddingProvider:
    """Factory for RAG embedding provider."""
    raw_type = provider_type or os.getenv("EMBEDDING_PROVIDER") or "local"
    ptype = raw_type.lower()

    if ptype == "external" or ptype == "openai":
        return ExternalAPIEmbeddingProvider()

    # Default to local deterministic provider for reproducibility and offline testing
    return DeterministicLocalEmbeddingProvider()
