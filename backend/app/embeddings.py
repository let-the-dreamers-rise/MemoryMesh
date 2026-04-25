from __future__ import annotations

import hashlib
import math

from .chunking import tokenize


class EmbeddingService:
    """Local embedding service with a deterministic fallback for demos."""

    dimension = 384

    def __init__(self, mode: str = "auto") -> None:
        self.mode = "hash"
        self.model_name = "hashing-384"
        self._model = None

        if mode.lower() != "hash":
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
                self.mode = "minilm"
                self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
            except Exception:
                if mode.lower() == "minilm":
                    raise

    def encode(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        if self._model is not None:
            vectors = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            return [list(map(float, vector)) for vector in vectors]

        return [self._hash_embedding(text) for text in texts]

    def encode_one(self, text: str) -> list[float]:
        return self.encode([text])[0]

    def _hash_embedding(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = tokenize(text)
        if not tokens:
            tokens = ["empty"]

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            first = int.from_bytes(digest[:8], "big")
            second = int.from_bytes(digest[8:16], "big")
            index = first % self.dimension
            sign = 1.0 if second % 2 == 0 else -1.0
            weight = 1.0 + min(len(token), 18) / 18.0
            vector[index] += sign * weight

        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

