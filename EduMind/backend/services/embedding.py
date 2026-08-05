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
from services.model_config import model_config_service

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service to generate vector representations of text queries or resources."""

    async def get_embedding(self, text: str) -> list[float]:
        """单条 embedding。"""
        results = await self.get_embeddings([text])
        return results[0]

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        批量 embedding。返回顺序与输入一致。

        API key 缺失时使用确定性 hash 伪向量（同文本永远同向量）。
        """
        runtime = model_config_service.runtime
        api_key = runtime.embedding_api_key
        dimensions = runtime.embedding_dimensions

        # Offline Mock Fallback
        if not api_key:
            return [self._mock_vector(t, dimensions) for t in texts]

        # Online HTTP Request (OpenAI-compatible)
        url = f"{runtime.embedding_base_url.rstrip('/')}/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": runtime.embedding_model,
            "input": texts,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    logger.error(
                        f"Embedding API returned status {response.status_code}: {response.text}"
                    )
                    raise ServiceUnavailableError("Embedding Service API")

                result = response.json()
                # 按 index 排序，保持与输入顺序一致
                items = sorted(result["data"], key=lambda x: x.get("index", 0))
                return [item["embedding"] for item in items]

        except Exception as exc:
            if isinstance(exc, ServiceUnavailableError):
                raise
            logger.error(f"Failed calling embedding API: {exc}", exc_info=True)
            raise ServiceUnavailableError("Embedding Service Connection")

    @staticmethod
    def _mock_vector(text: str, dimensions: int) -> list[float]:
        """确定性伪向量（同文本永远同向量）。"""
        seed = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16)
        rng = random.Random(seed)
        vec = [rng.uniform(-1.0, 1.0) for _ in range(dimensions)]
        norm = sum(x**2 for x in vec) ** 0.5
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec


# Singleton instance
embedding_service = EmbeddingService()
