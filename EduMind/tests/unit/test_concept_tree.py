"""
Unit Tests for Concept Tree (skill tree) builder.

Tests are fully offline — uses in-memory SQLite, no Qdrant, no LLM.
"""

import sys
import unittest
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from models import Base
from config.settings import settings
from rag import rag_module
from rag.concept_tree import extract_key_points, build_concept_tree_for_topic
from services.model_config import model_config_service


class TestExtractKeyPoints(unittest.TestCase):
    """Verify key-point extraction from content text."""

    def test_basic_extraction(self):
        content = "一元二次方程的求根公式是 x = (-b ± √(b²-4ac)) / 2a。判别式 Δ = b² - 4ac 决定根的个数。"
        points = extract_key_points(content, limit=5)
        self.assertGreater(len(points), 0)
        self.assertLessEqual(len(points), 5)

    def test_empty_content(self):
        self.assertEqual(extract_key_points(""), [])
        self.assertEqual(extract_key_points(None), [])
        self.assertEqual(extract_key_points("   "), [])

    def test_short_content_filtered(self):
        # Fragments shorter than 8 chars after sentence split should be filtered
        points = extract_key_points("好。测试。ab。")
        self.assertEqual(points, [])

    def test_limit_respected(self):
        content = "。".join([f"这是一个足够长的知识点描述第{i}条内容" for i in range(10)])
        points = extract_key_points(content, limit=3)
        self.assertLessEqual(len(points), 3)

    def test_dedup(self):
        content = "求根公式用于求解方程。求根公式用于求解方程。求根公式用于求解方程。"
        points = extract_key_points(content)
        # Duplicates should be removed
        self.assertLessEqual(len(points), 1)


class TestBuildConceptTree(unittest.IsolatedAsyncioTestCase):
    """Verify concept tree construction from DB resources."""

    async def asyncSetUp(self) -> None:
        self.original_settings = {
            "qdrant_path": settings.qdrant_path,
            "embedding_dimensions": settings.embedding_dimensions,
            "embedding_api_key": settings.embedding_api_key,
        }
        self.original_runtime = model_config_service.runtime

        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.async_session_factory = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False,
        )
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.db = self.async_session_factory()

        import shutil
        self.test_qdrant_path = (
            Path(__file__).resolve().parent / "test_data" / "test_qdrant_tree"
        )
        shutil.rmtree(self.test_qdrant_path, ignore_errors=True)
        settings.qdrant_path = str(self.test_qdrant_path)
        settings.embedding_dimensions = 384
        settings.embedding_api_key = ""
        model_config_service.reset_to_environment()
        rag_module._client = None

    async def asyncTearDown(self) -> None:
        await self.db.close()
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.engine.dispose()
        if rag_module._client:
            await rag_module._client.close()
            rag_module._client = None
        import shutil
        if self.test_qdrant_path.exists():
            shutil.rmtree(self.test_qdrant_path, ignore_errors=True)
        for name, value in self.original_settings.items():
            setattr(settings, name, value)
        model_config_service._runtime = self.original_runtime

    async def test_tree_with_resources(self):
        """Tree should have branches from grouped parent docs."""
        await rag_module.upsert_resource(
            db=self.db, title="代数基础", subject="数学",
            topic="代数", content="变量是用字母表示的数，如 x 和 y。方程是含有未知数的等式。",
        )
        await rag_module.upsert_resource(
            db=self.db, title="几何入门", subject="数学",
            topic="代数", content="点线面是几何的基本元素。角由两条射线组成。",
        )
        await self.db.commit()

        tree = await build_concept_tree_for_topic(self.db, topic="代数")
        self.assertEqual(tree["topic"], "代数")
        self.assertGreater(tree["resource_count"], 0)
        self.assertGreater(len(tree["children"]), 0)
        # Each child should have leaves (key points)
        for child in tree["children"]:
            self.assertIn("label", child)
            self.assertIn("children", child)

    async def test_empty_topic(self):
        """Empty topic should return an empty tree."""
        tree = await build_concept_tree_for_topic(self.db, topic="")
        self.assertEqual(tree["children"], [])
        self.assertEqual(tree["resource_count"], 0)

    async def test_no_matching_resources(self):
        """Topic with no resources should return empty children."""
        await rag_module.upsert_resource(
            db=self.db, title="代数", subject="数学",
            topic="代数", content="变量和方程的基本概念。",
        )
        await self.db.commit()

        tree = await build_concept_tree_for_topic(self.db, topic="不存在的主题")
        self.assertEqual(tree["children"], [])
        self.assertEqual(tree["resource_count"], 0)


if __name__ == "__main__":
    unittest.main()
