"""
EduMind Embedding Service

Converts text strings into high-dimensional vector embeddings.
Supports OpenAI-compatible REST APIs with an offline deterministic hash fallback.
"""

import hashlib
import logging
import random
import httpx
from config.settings import settings
from core.exceptions import ServiceUnavailableError

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service to generate vector representations of text queries or resources."""

    async def get_embedding(self, text: str) -> list[float]:
        """
        Generate embedding vector for a given string query.

        If embedding_api_key is not configured in settings, falls back to
        an offline, deterministic L2-normalized pseudo-random generator
        (so matching strings always produce identical vectors of fixed length).
        """
        api_key = settings.embedding_api_key
        dimensions = settings.embedding_dimensions

        # Offline Mock Fallback
        if not api_key:
            logger.debug(
                f"No EMBEDDING_API_KEY set. Generating deterministic mock vector ({dimensions} dims)."
            )
            # Create a seed based on the string MD5 hash
            seed = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16)
            rng = random.Random(seed)

            # Generate vector values between -1.0 and 1.0
            vector = [rng.uniform(-1.0, 1.0) for _ in range(dimensions)]

            # L2 Normalization (make it a unit vector)
            norm = sum(x**2 for x in vector) ** 0.5
            if norm > 0:
                vector = [x / norm for x in vector]

            return vector

        # Online HTTP Request (OpenAI-compatible)
        url = f"{settings.embedding_base_url.rstrip('/')}/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.embedding_model,
            "input": text,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    logger.error(
                        f"Embedding API returned status {response.status_code}: {response.text}"
                    )
                    raise ServiceUnavailableError("Embedding Service API")

                result = response.json()
                embedding = result["data"][0]["embedding"]

                # Ensure dimensions match expected size (truncate or pad if necessary, or just return)
                return embedding

        except Exception as exc:
            if isinstance(exc, ServiceUnavailableError):
                raise
            logger.error(f"Failed calling embedding API: {exc}", exc_info=True)
            raise ServiceUnavailableError("Embedding Service Connection")


# Singleton instance
embedding_service = EmbeddingService()
