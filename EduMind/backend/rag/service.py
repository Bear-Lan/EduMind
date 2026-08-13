"""
EduMind Retrieval-Augmented Generation (RAG) Module

Manages vector searches in Qdrant and metadata retrieval in PostgreSQL.
"""

import logging
import re
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from qdrant_client import AsyncQdrantClient, models

from config.settings import settings
from models.resource import LearningResource
from services.embedding import embedding_service
from core.exceptions import ServiceUnavailableError
from services.model_config import model_config_service
from rag.filters import (
    extract_stage,
    extract_subject_key,
    parse_resource_subject,
    resource_matches_scope,
    stage_from_grade,
)
from rag.rerank import rerank_keyword_overlap
from rag.hybrid import (
    extract_precise_terms,
    keyword_search,
    reciprocal_rank_fusion,
)
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
        """Verify the Qdrant collection exists; creates it if not present.

        Also validates that an existing collection's vector dimensions match
        the current runtime embedding config — a mismatch will cause search
        failures and is logged loudly.
        """
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
            else:
                # Validate dimension match for existing collection
                try:
                    info = await client.get_collection(collection_name)
                    vectors = info.config.params.vectors
                    # vectors can be a single VectorParams or a dict of named vectors
                    if isinstance(vectors, dict):
                        existing_size = next(iter(vectors.values())).size
                    else:
                        existing_size = vectors.size
                    expected = model_config_service.runtime.embedding_dimensions
                    if int(existing_size) != int(expected):
                        logger.error(
                            f"⚠️  Qdrant collection '{collection_name}' has "
                            f"vector size {existing_size} but settings expect "
                            f"{expected}. Delete data/qdrant_storage and re-seed."
                        )
                except Exception as dim_exc:
                    logger.debug(f"Could not validate collection dimensions: {dim_exc}")
        except Exception as exc:
            logger.error(
                f"Failed to ensure Qdrant collection '{collection_name}': {exc}"
            )
            raise ServiceUnavailableError("Vector Database")

    def _build_scope_filter(
        self,
        subject_key: str | None,
        stage: str | None,
        *,
        require_stage: bool = False,
    ) -> models.Filter | None:
        """
        Build a Qdrant payload filter.

        Matches either normalized subject_key (new upserts) OR legacy
        subject strings like "高中 数学" (old seed points).
        """
        if not subject_key and not (stage and require_stage):
            return None

        must: list = []

        if subject_key:
            subject_should: list = [
                models.FieldCondition(
                    key="subject_key",
                    match=models.MatchValue(value=subject_key),
                ),
                models.FieldCondition(
                    key="subject",
                    match=models.MatchValue(value=subject_key),
                ),
            ]
            for st in ("小学", "初中", "高中", "大学", "职业"):
                subject_should.append(
                    models.FieldCondition(
                        key="subject",
                        match=models.MatchValue(value=f"{st} {subject_key}"),
                    )
                )
                subject_should.append(
                    models.FieldCondition(
                        key="subject",
                        match=models.MatchValue(value=f"{st}{subject_key}"),
                    )
                )
            must.append(models.Filter(should=subject_should))

        if stage and require_stage:
            stage_should = [
                models.FieldCondition(
                    key="stage",
                    match=models.MatchValue(value=stage),
                ),
            ]
            if subject_key:
                stage_should.append(
                    models.FieldCondition(
                        key="subject",
                        match=models.MatchValue(value=f"{stage} {subject_key}"),
                    )
                )
                stage_should.append(
                    models.FieldCondition(
                        key="subject",
                        match=models.MatchValue(value=f"{stage}{subject_key}"),
                    )
                )
            must.append(models.Filter(should=stage_should))

        return models.Filter(must=must) if must else None

    async def search(
        self,
        query_vector: list[float],
        limit: int = 3,
        subject_key: str | None = None,
        stage: str | None = None,
        require_stage: bool = False,
    ) -> list[tuple[str, float]]:
        """
        Query Qdrant; optional subject_key / stage narrow via payload filter.

        Returns list of (point_id, score) tuples ranked by similarity (highest first).
        """
        client = self.get_client()
        await self._ensure_collection(client)

        query_filter = self._build_scope_filter(
            subject_key, stage, require_stage=require_stage
        )

        try:
            results = await client.search(
                collection_name=settings.qdrant_collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit,
            )
            scored: list[tuple[str, float]] = []
            for point in results:
                raw = float(point.score) if hasattr(point, "score") else 0.0
                sim = (raw + 1.0) / 2.0 if raw < 1.0 else raw
                scored.append((str(point.id), sim))
            return scored
        except Exception as exc:
            logger.error(f"Failed to search Qdrant index: {exc}")
            raise ServiceUnavailableError("Vector Database Query")

    async def retrieve_scored(
        self,
        db: AsyncSession,
        query: str,
        limit: int | None = None,
        score_threshold: float | None = None,
        subject: str | None = None,
        grade: str | None = None,
        require_stage: bool = False,
        recall_limit: int | None = None,
    ) -> list[tuple[LearningResource, float]]:
        """
        Hybrid retrieval pipeline:
          A) Vector recall Top-N + keyword/exact-term recall (题号/公式名/专名)
          B) RRF fuse the two channels
          C) Lexical+vector rerank → Top-K

        Returned score is the fused rerank score.
        """
        if score_threshold is None:
            score_threshold = settings.rag_score_threshold
        if limit is None:
            limit = settings.rag_rerank_top_k
        if recall_limit is None:
            recall_limit = settings.rag_recall_limit

        subject_key = extract_subject_key(subject)
        stage = stage_from_grade(grade) or extract_stage(subject)

        query_vector = await embedding_service.get_embedding(query)

        # ── Channel 1: vector recall ─────────────────────────────────────
        fetch_limit = max(int(recall_limit), int(limit) * 4, 12)
        scored = await self.search(
            query_vector,
            limit=fetch_limit,
            subject_key=subject_key,
            stage=stage,
            require_stage=require_stage,
        )

        if not scored and subject_key and stage and not require_stage:
            logger.info(
                "RAG retrieve: no hits for subject=%s stage=%s; retry subject-only",
                subject_key,
                stage,
            )
            scored = await self.search(
                query_vector,
                limit=fetch_limit,
                subject_key=subject_key,
                stage=None,
                require_stage=False,
            )

        score_map = {pid: sim for pid, sim in scored}
        best = max(score_map.values()) if score_map else 0.0
        # Band near the best hit, but never open the floor when overall quality is poor
        if best > 0:
            soft_floor = max(
                score_threshold * 0.75,
                min(score_threshold, best * 0.85),
            )
        else:
            soft_floor = score_threshold
        kept_ids = [pid for pid, sim in scored if sim >= soft_floor]

        vector_rows: list[LearningResource] = []
        if kept_ids:
            results = await db.scalars(
                select(LearningResource).where(
                    LearningResource.embedding_id.in_(kept_ids)
                )
            )
            resource_map = {r.embedding_id: r for r in results}
            for eid in kept_ids:
                res = resource_map.get(eid)
                if not res:
                    continue
                if not resource_matches_scope(
                    res.subject,
                    subject_key,
                    stage,
                    require_stage=require_stage,
                ):
                    continue
                vector_rows.append(res)

        if stage and not require_stage and vector_rows:
            explicit = [
                r
                for r in vector_rows
                if parse_resource_subject(r.subject)[1] == stage
            ]
            if explicit:
                vector_rows = explicit

        # ── Channel 2: keyword / exact-term recall ────────────────────────
        keyword_rows: list[tuple[LearningResource, float]] = []
        if settings.rag_hybrid_enabled:
            keyword_rows = await keyword_search(
                db,
                query,
                limit=settings.rag_keyword_limit,
                subject_key=subject_key,
                stage=stage,
                require_stage=require_stage,
            )
            if stage and not require_stage and keyword_rows:
                explicit_kw = [
                    (r, s)
                    for r, s in keyword_rows
                    if parse_resource_subject(r.subject)[1] == stage
                ]
                if explicit_kw:
                    keyword_rows = explicit_kw

        if not vector_rows and not keyword_rows:
            logger.info(
                "RAG hybrid: empty vector+keyword recall (terms=%s)",
                extract_precise_terms(query)[:5],
            )
            return []

        # ── Fuse via RRF (or single channel) ──────────────────────────────
        by_id: dict[int, LearningResource] = {}
        for r in vector_rows:
            by_id[r.id] = r
        for r, _ in keyword_rows:
            by_id[r.id] = r

        vector_ids = [r.id for r in vector_rows]
        keyword_ids = [r.id for r, _ in keyword_rows]

        if vector_ids and keyword_ids:
            fused = reciprocal_rank_fusion(
                [vector_ids, keyword_ids],
                k=settings.rag_hybrid_rrf_k,
                weights=[
                    settings.rag_hybrid_vector_weight,
                    settings.rag_hybrid_keyword_weight,
                ],
            )
            # Seed rerank with a blended prior: RRF-normalized + vector/keyword raw
            rrf_max = fused[0][1] if fused else 1.0
            kw_score_map = {r.id: s for r, s in keyword_rows}
            ordered: list[tuple[LearningResource, float]] = []
            for rid, rrf in fused:
                res = by_id.get(rid)
                if not res:
                    continue
                vec = float(score_map.get(res.embedding_id or "", 0.0))
                kw = float(kw_score_map.get(rid, 0.0))
                # Prior for rerank: emphasize exact hits when present
                prior = 0.5 * (rrf / rrf_max if rrf_max else 0.0) + 0.3 * vec + 0.2 * kw
                ordered.append((res, prior))
            logger.info(
                "RAG hybrid: vector=%d keyword=%d fused=%d terms=%s",
                len(vector_ids),
                len(keyword_ids),
                len(ordered),
                extract_precise_terms(query)[:5],
            )
        elif vector_ids:
            ordered = [
                (r, float(score_map.get(r.embedding_id or "", 0.0)))
                for r in vector_rows
            ]
        else:
            ordered = list(keyword_rows)

        if not ordered:
            return []

        # ── Rerank → Top-K ────────────────────────────────────────────────
        reranked = self.rerank_scored(ordered, query=query, top_k=int(limit))

        gate = score_threshold * 0.9
        strong = [(r, s) for r, s in reranked if s >= gate]
        if not strong:
            # Precise-term path: only relax when keyword channel itself is strong
            # (avoids "抽到词就强制 Top-K" 的弱相关放行)
            kw_map = {r.id: float(s) for r, s in keyword_rows}
            min_kw = float(settings.rag_keyword_relax_min_score)
            strong = [
                (r, s)
                for r, s in reranked
                if kw_map.get(r.id, 0.0) >= min_kw
            ][: int(limit)]
            if not strong:
                logger.info(
                    "RAG rerank: top fused score %.3f below gate %.2f "
                    "(no strong keyword hit ≥ %.2f) — empty context",
                    reranked[0][1] if reranked else 0.0,
                    gate,
                    min_kw,
                )
                return []
            logger.info(
                "RAG hybrid: relaxed gate via strong keyword hits (%d)",
                len(strong),
            )
        return strong

    async def retrieve(
        self,
        db: AsyncSession,
        query: str,
        limit: int | None = None,
        score_threshold: float | None = None,
        subject: str | None = None,
        grade: str | None = None,
        require_stage: bool = False,
    ) -> list[LearningResource]:
        """Retrieve relevant learning resources (scores discarded)."""
        scored = await self.retrieve_scored(
            db,
            query=query,
            limit=limit,
            score_threshold=score_threshold,
            subject=subject,
            grade=grade,
            require_stage=require_stage,
        )
        return [res for res, _ in scored]

    def rerank(self, resources: list[LearningResource]) -> list[LearningResource]:
        """Legacy pass-through (prefer rerank_scored with query)."""
        return resources

    def rerank_scored(
        self,
        items: list[tuple[LearningResource, float]],
        query: str = "",
        top_k: int | None = None,
    ) -> list[tuple[LearningResource, float]]:
        """
        Rerank vector hits with keyword overlap fusion.

        Falls back to vector order when query is empty.
        """
        if top_k is None:
            top_k = settings.rag_rerank_top_k
        if not items:
            return []
        if not (query or "").strip():
            return items[: max(1, int(top_k))]

        return rerank_keyword_overlap(
            query,
            items,
            top_k=int(top_k),
            vector_weight=settings.rag_rerank_vector_weight,
        )
    @staticmethod
    def make_snippet(content: str, query: str = "", max_len: int = 140) -> str:
        """
        Build a short snippet for citation UI.

        Prefer a window around the first query token hit; else lead text.
        """
        text = re.sub(r"\s+", " ", (content or "")).strip()
        if not text:
            return ""
        if len(text) <= max_len:
            return text

        anchor = -1
        for token in re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z0-9]{3,}", query or ""):
            idx = text.casefold().find(token.casefold())
            if idx >= 0:
                anchor = idx
                break

        if anchor < 0:
            return text[: max_len - 1].rstrip() + "…"

        start = max(0, anchor - max_len // 3)
        end = min(len(text), start + max_len)
        start = max(0, end - max_len)
        snippet = text[start:end].strip()
        if start > 0:
            snippet = "…" + snippet
        if end < len(text):
            snippet = snippet + "…"
        return snippet

    def build_references(
        self,
        scored_resources: list[tuple[LearningResource, float]],
        query: str = "",
    ) -> list[dict]:
        """Serialize scored hits for chat / search citation UI."""
        max_chars = max(200, int(settings.rag_reference_content_max_chars))
        refs: list[dict] = []
        for res, score in scored_resources:
            content = res.content or ""
            if len(content) > max_chars:
                content_out = content[:max_chars].rstrip() + "…"
            else:
                content_out = content
            refs.append(
                {
                    "id": res.id,
                    "title": res.title,
                    "topic": res.topic,
                    "subject": res.subject,
                    "source": res.source,
                    "parent_doc": res.parent_doc or res.title,
                    "chapter": res.chapter,
                    "section": res.section,
                    "chunk_index": int(res.chunk_index or 0),
                    # Fused retrieval score (vector/keyword/rerank), not raw cosine
                    "score": round(float(score), 4),
                    "snippet": self.make_snippet(content, query=query),
                    "content": content_out,
                }
            )
        return refs

    def build_context(self, resources: list[LearningResource]) -> str:
        """Format learning resources into a prompt context block."""
        context_blocks = []
        for idx, res in enumerate(resources, 1):
            loc_parts = [
                p
                for p in (
                    res.parent_doc or res.title,
                    res.chapter,
                    res.section,
                )
                if p
            ]
            loc = " > ".join(loc_parts) if loc_parts else res.title
            block = (
                f"[Document {idx}]: {loc} | Subject: {res.subject} | Topic: {res.topic}\n"
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
        chapter: str | None = None,
        section: str | None = None,
        chunk: bool = True,
    ) -> LearningResource:
        """
        Ingest a document; by default splits into chunks and returns the first chunk row.
        Prefer upsert_document() when you need all chunk rows.
        """
        rows = await self.upsert_document(
            db,
            title=title,
            subject=subject,
            topic=topic,
            content=content,
            source=source,
            chapter=chapter,
            section=section,
            chunk=chunk,
        )
        return rows[0]

    async def upsert_document(
        self,
        db: AsyncSession,
        title: str,
        subject: str,
        topic: str,
        content: str,
        source: str | None = None,
        chapter: str | None = None,
        section: str | None = None,
        chunk: bool = True,
    ) -> list[LearningResource]:
        """
        Ingest a full document as one or more indexed chunks.

        Each chunk row/Qdrant point carries:
          parent_doc, chapter, section, chunk_index
        plus subject_key / stage for scoped retrieval.
        """
        from rag.document_processor import chunk_document

        client = self.get_client()
        await self._ensure_collection(client)

        subject_key, stage = parse_resource_subject(subject)
        parent_doc = title

        if chunk:
            pieces = chunk_document(
                content or "",
                chunk_size=settings.rag_chunk_size,
                overlap=settings.rag_chunk_overlap,
                default_chapter=chapter,
                default_section=section,
            )
        else:
            from rag.document_processor import TextChunk

            pieces = [
                TextChunk(
                    text=(content or "").strip(),
                    chapter=chapter,
                    section=section,
                    chunk_index=0,
                )
            ]

        if not pieces:
            raise ValueError("Cannot index empty document content")

        created: list[LearningResource] = []
        for piece in pieces:
            point_id = str(uuid.uuid4())
            vector = await embedding_service.get_embedding(piece.text)

            chunk_title = title
            if len(pieces) > 1:
                chunk_title = f"{title} ·#{piece.chunk_index + 1}"

            try:
                await client.upsert(
                    collection_name=settings.qdrant_collection_name,
                    points=[
                        models.PointStruct(
                            id=point_id,
                            vector=vector,
                            payload={
                                "title": chunk_title,
                                "parent_doc": parent_doc,
                                "chapter": piece.chapter,
                                "section": piece.section,
                                "chunk_index": piece.chunk_index,
                                "subject": subject,
                                "subject_key": subject_key,
                                "stage": stage,
                                "topic": topic,
                                "source": source,
                            },
                        )
                    ],
                )
            except Exception as exc:
                logger.error(f"Failed to upsert chunk to Qdrant: {exc}")
                raise ServiceUnavailableError("Vector Database Ingestion")

            resource = LearningResource(
                title=chunk_title,
                subject=subject,
                topic=topic,
                source=source,
                embedding_id=point_id,
                content=piece.text,
                parent_doc=parent_doc,
                chapter=piece.chapter,
                section=piece.section,
                chunk_index=piece.chunk_index,
            )
            db.add(resource)
            created.append(resource)

        await db.flush()
        logger.info(
            "Indexed document '%s' as %d chunk(s) "
            "(subject_key=%s, stage=%s, first Postgres ID=%s)",
            parent_doc,
            len(created),
            subject_key,
            stage,
            created[0].id,
        )
        return created
