"""
Unit Tests for RAG Module and Embedding Service

Verifies embedding generation (mock fallback) and vector retrieval/database mappings.
"""

import sys
import os
import shutil
import unittest
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Add backend directory to sys.path so we can import local modules
backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from models import Base
from config.settings import settings
from services.embedding import embedding_service
from rag import rag_module
from services.model_config import model_config_service


class TestRAGAndEmbedding(unittest.IsolatedAsyncioTestCase):
    """Asynchronous unit/integration tests for EmbeddingService and RAGModule."""

    async def asyncSetUp(self) -> None:
        self.original_settings = {
            "qdrant_path": settings.qdrant_path,
            "embedding_dimensions": settings.embedding_dimensions,
            "embedding_api_key": settings.embedding_api_key,
        }
        self.original_runtime = model_config_service.runtime

        # 1. Database Setup (SQLite in-memory)
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.async_session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.db = self.async_session_factory()

        # 2. Qdrant Setup (Local Path Mode)
        self.test_qdrant_path = (
            Path(__file__).resolve().parent / "test_data" / "test_qdrant_db"
        )
        shutil.rmtree(self.test_qdrant_path, ignore_errors=True)
        # Force config settings to use the local test path
        settings.qdrant_path = str(self.test_qdrant_path)
        settings.embedding_dimensions = 384  # Force dimensions to 384 for fast tests
        settings.embedding_api_key = ""  # Tests must never call the live embedding API
        model_config_service.reset_to_environment()

        # Instantiate fresh Qdrant client for testing
        rag_module._client = None
        self.qclient = rag_module.get_client()

    async def asyncTearDown(self) -> None:
        # Close database session
        await self.db.close()
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.engine.dispose()

        # Close Qdrant connection and clean up database files
        if rag_module._client:
            await rag_module._client.close()
            rag_module._client = None

        # Delete local Qdrant DB directory
        if self.test_qdrant_path.exists():
            shutil.rmtree(self.test_qdrant_path, ignore_errors=True)

        for name, value in self.original_settings.items():
            setattr(settings, name, value)
        model_config_service._runtime = self.original_runtime

    async def test_embedding_service_offline_fallback(self) -> None:
        """Verify the offline mock embedding generator properties."""
        text1 = "Introduction to Quadratic Equations"
        text2 = "How to solve linear inequalities"

        vector1 = await embedding_service.get_embedding(text1)
        vector1_again = await embedding_service.get_embedding(text1)
        vector2 = await embedding_service.get_embedding(text2)

        # Dimension validation
        self.assertEqual(len(vector1), 384)
        self.assertEqual(len(vector2), 384)

        # Determinism check (same text yields identical vector)
        self.assertEqual(vector1, vector1_again)

        # Distinctness check (different text yields different vector)
        self.assertNotEqual(vector1, vector2)

        # L2 Norm check (unit length normalization)
        norm = sum(x**2 for x in vector1) ** 0.5
        self.assertAlmostEqual(norm, 1.0, places=5)

    async def test_rag_upsert_and_retrieve(self) -> None:
        """Verify upserting documents and retrieving them via query similarity."""
        # 1. Ingest resource segments
        res1 = await rag_module.upsert_resource(
            db=self.db,
            title="Algebra Basics",
            subject="Mathematics",
            topic="Introduction to Algebra",
            content="Algebra uses variables like x and y to solve equations and represent relations.",
            source="Curriculum Textbook Vol. 1",
        )
        res2 = await rag_module.upsert_resource(
            db=self.db,
            title="Geometry Definitions",
            subject="Mathematics",
            topic="Basic Geometry",
            content="Geometry studies lines, angles, shapes, and properties of coordinate planes.",
            source="Curriculum Textbook Vol. 2",
        )
        await self.db.commit()

        # Assert database IDs are generated and vector IDs are set
        self.assertIsNotNone(res1.id)
        self.assertIsNotNone(res1.embedding_id)
        self.assertIsNotNone(res2.id)
        self.assertIsNotNone(res2.embedding_id)

        # 2. Run retrieval search
        # Search query matching Algebra Basics (exact match to ensure highest similarity in mock mode)
        results = await rag_module.retrieve(
            db=self.db,
            query="Algebra uses variables like x and y to solve equations and represent relations.",
            limit=1,
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Algebra Basics")
        self.assertEqual(
            results[0].content,
            "Algebra uses variables like x and y to solve equations and represent relations.",
        )

        # Search query matching Geometry Definitions (exact match to ensure highest similarity in mock mode)
        results2 = await rag_module.retrieve(
            db=self.db,
            query="Geometry studies lines, angles, shapes, and properties of coordinate planes.",
            limit=1,
        )
        self.assertEqual(len(results2), 1)
        self.assertEqual(results2[0].title, "Geometry Definitions")

    async def test_build_context(self) -> None:
        """Verify the built prompt context string layout."""
        res1 = await rag_module.upsert_resource(
            db=self.db,
            title="Algebra Basics",
            subject="Math",
            topic="Algebra",
            content="Algebra content details.",
        )
        await self.db.commit()

        context_string = rag_module.build_context([res1])
        # New format: [Document 1]: {loc} | Subject: ... | Topic: ...\nContent: ...
        self.assertIn("[Document 1]:", context_string)
        self.assertIn("Algebra Basics", context_string)
        self.assertIn("Subject: Math", context_string)
        self.assertIn("Topic: Algebra", context_string)
        self.assertIn("Content: Algebra content details.", context_string)


if __name__ == "__main__":
    unittest.main()
