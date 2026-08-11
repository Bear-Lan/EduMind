"""
EduMind Retrieval-Augmented Generation (RAG) Module

Manages vector searches in Qdrant and metadata retrieval in PostgreSQL.
"""

import logging
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from qdrant_client import AsyncQdrantClient, models

from config.settings import settings
from models.resource import LearningResource
from services.embedding import embedding_service
from core.exceptions import ServiceUnavailableError
from services.model_config import model_config_service

logger = logging.getLogger(__name__)


class RAGModule:
    """Manages index upserts, Qdrant vector searches, and PostgreSQL resource retrieval."""

    def __init__(self) -> None:
        self._client: AsyncQdrantClient | None = None

    def get_client(self) -> AsyncQdrantClient:
        """Initialize or return the cached AsyncQdrantClient instance."""
        if self._client is None:
            if settings.qdrant_path == ":memory:":
                logger.info("Initializing Qdrant AsyncClient in In-Memory Mode")
                self._client = AsyncQdrantClient(location=":memory:")
            elif settings.qdrant_path:
                logger.info(
                    f"Initializing Qdrant AsyncClient in Local Mode (path: {settings.qdrant_path})"
                )
                self._client = AsyncQdrantClient(path=settings.qdrant_path)
            else:
                logger.info(
                    f"Initializing Qdrant AsyncClient in Server Mode (host: {settings.qdrant_host}:{settings.qdrant_port})"
                )
                self._client = AsyncQdrantClient(
                    host=settings.qdrant_host,
                    port=settings.qdrant_port,
                )
        return self._client

    async def _ensure_collection(self, client: AsyncQdrantClient) -> None:
        """Verify the Qdrant collection exists; creates it if not present."""
        collection_name = settings.qdrant_collection_name
        try:
            collections_response = await client.get_collections()
            existing_names = [col.name for col in collections_response.collections]

            if collection_name not in existing_names:
                logger.info(f"Creating Qdrant collection: {collection_name}")
                await client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=model_config_service.runtime.embedding_dimensions,
                        distance=models.Distance.COSINE,
                    ),
                )
        except Exception as exc:
            logger.error(
                f"Failed to ensure Qdrant collection '{collection_name}': {exc}"
            )
            raise ServiceUnavailableError("Vector Database")

    async def search(self, query_vector: list[float], limit: int = 3) -> list[tuple[str, float]]:
        """
        Query Qdrant collection using the query vector.

        Returns list of (point_id, score) tuples ranked by similarity (highest first).
        Qdrant cosine distance is converted to similarity in [0,1].
        """
        client = self.get_client()
        await self._ensure_collection(client)

        try:
            results = await client.search(
                collection_name=settings.qdrant_collection_name,
                query_vector=query_vector,
                limit=limit,
            )
            scored: list[tuple[str, float]] = []
            for point in results:
                # Qdrant returns `score` which for Cosine distance is in [-1, 1]
                # (higher = more similar). Normalize to [0, 1].
                raw = float(point.score) if hasattr(point, "score") else 0.0
                sim = (raw + 1.0) / 2.0 if raw < 1.0 else raw
                scored.append((str(point.id), sim))
            # Already ranked by Qdrant; keep order
            return scored
        except Exception as exc:
            logger.error(f"Failed to search Qdrant index: {exc}")
            raise ServiceUnavailableError("Vector Database Query")

    async def retrieve(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 3,
        score_threshold: float | None = None,
    ) -> list[LearningResource]:
        """
        Retrieve relevant learning resources, filtered by similarity threshold.

        - Drops hits with similarity < score_threshold.
        - Returns [] when nothing passes (caller should treat as "no context").
        """
        if score_threshold is None:
            score_threshold = settings.rag_score_threshold

        # 1. Generate Query Embedding
        query_vector = await embedding_service.get_embedding(query)

        # 2. Search Qdrant (with scores)
        scored = await self.search(query_vector, limit=limit)
        if not scored:
            return []

        # Filter by similarity threshold
        kept_ids = [pid for pid, sim in scored if sim >= score_threshold]
        if not kept_ids:
            logger.info(
                "RAG retrieve: no hits above threshold %.2f (best=%.3f)",
                score_threshold,
                max((s for _, s in scored), default=0.0),
            )
            return []

        # 3. Retrieve entities from PostgreSQL
        results = await db.scalars(
            select(LearningResource).where(
                LearningResource.embedding_id.in_(kept_ids)
            )
        )

        # Re-order based on Qdrant similarity rank
        resource_map = {r.embedding_id: r for r in results}
        ordered_resources = [
            resource_map[eid] for eid in kept_ids if eid in resource_map
        ]

        # 4. Rerank (MVP pass-through)
        return self.rerank(ordered_resources)

    def rerank(self, resources: list[LearningResource]) -> list[LearningResource]:
        """
        Rerank retrieved resources (MVP pass-through).
        """
        return resources

    def build_context(self, resources: list[LearningResource]) -> str:
        """
        Format a list of learning resources into a clean prompt context block for LLM execution.
        """
        context_blocks = []
        for idx, res in enumerate(resources, 1):
            block = (
                f"[Document {idx}]: Title: {res.title} | Topic: {res.topic}\n"
                f"Content: {res.content}"
            )
            context_blocks.append(block)

        return "\n\n".join(context_blocks)

    async def upsert_resource(
        self,
        db: AsyncSession,
        title: str,
        subject: str,
        topic: str,
        content: str,
        source: str | None = None,
    ) -> LearningResource:
        """
        Ingest a new segment/document into the retrieval index.

        Runs: embedding -> Qdrant index insertion -> relational DB entity creation.
        """
        client = self.get_client()
        await self._ensure_collection(client)

        # Generate unique Qdrant point UUID
        point_id = str(uuid.uuid4())

        # 1. Compute Content Embedding
        vector = await embedding_service.get_embedding(content)

        # 2. Insert into Qdrant
        try:
            await client.upsert(
                collection_name=settings.qdrant_collection_name,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "title": title,
                            "subject": subject,
                            "topic": topic,
                            "source": source,
                        },
                    )
                ],
            )
        except Exception as exc:
            logger.error(f"Failed to upsert point to Qdrant: {exc}")
            raise ServiceUnavailableError("Vector Database Ingestion")

        # 3. Create ORM Entity in Postgres
        resource = LearningResource(
            title=title,
            subject=subject,
            topic=topic,
            source=source,
            embedding_id=point_id,
            content=content,
        )
        db.add(resource)
        await db.flush()

        logger.info(
            f"Successfully indexed resource '{title}' (Postgres ID: {resource.id}, Qdrant UUID: {point_id})"
        )
        return resource
