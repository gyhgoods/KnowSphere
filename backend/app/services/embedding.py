import hashlib
import json
import math
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings
from app.services.text_processing import tokenize_text


class EmbeddingServiceError(RuntimeError):
    pass


class EmbeddingService:
    def __init__(
        self,
        *,
        provider: str = settings.embedding_provider,
        model: str = settings.embedding_model,
        dimension: int = settings.embedding_dimension,
        base_url: str = settings.embedding_base_url,
    ) -> None:
        self.provider = provider
        self.model = model
        self.dimension = dimension
        self.base_url = base_url.rstrip("/")

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.provider == "hash":
            return [self._hash_embedding(text) for text in texts]
        if self.provider == "ollama":
            return self._ollama_embedding(texts)
        raise EmbeddingServiceError(f"Unsupported embedding provider: {self.provider}")

    def _hash_embedding(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = tokenize_text(text) or [text.lower()]
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=16).digest()
            for offset in range(0, len(digest), 4):
                value = int.from_bytes(digest[offset : offset + 4], "little")
                index = value % self.dimension
                vector[index] += 1.0 if value & 1 else -1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def _ollama_embedding(self, texts: list[str]) -> list[list[float]]:
        payload = json.dumps(
            {"model": self.model, "input": texts, "truncate": True}
        ).encode("utf-8")
        request = Request(
            f"{self.base_url}/api/embed",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(
                request, timeout=settings.embedding_timeout_seconds
            ) as response:
                result = json.load(response)
        except (HTTPError, URLError, TimeoutError) as exc:
            raise EmbeddingServiceError(f"Embedding service request failed: {exc}") from exc
        embeddings = result.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise EmbeddingServiceError("Embedding service returned an invalid response")
        for vector in embeddings:
            if len(vector) != self.dimension:
                raise EmbeddingServiceError(
                    f"Expected {self.dimension} dimensions, received {len(vector)}"
                )
        return embeddings


def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
