"""
Unit Tests for Magic Notes (notes-to-quiz) and AI Refusal logic.

Tests are fully offline — no live LLM API calls.
"""

import sys
import unittest
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from models import Base, ChatSession, ChatMessage
from config.settings import settings
from rag import rag_module
from llm import llm_service
from application.orchestrator import orchestrator
from services.model_config import model_config_service
from student_profile import student_profile_service


class TestMagicNotesOffline(unittest.IsolatedAsyncioTestCase):
    """Verify Magic Notes quiz generation in offline/mock mode."""

    async def asyncSetUp(self) -> None:
        self.original_runtime = model_config_service.runtime
        # Force mock mode: empty LLM key → generate_quiz_from_notes returns []
        from services.model_config import RuntimeModelConfig
        model_config_service._runtime = RuntimeModelConfig(
            llm_api_key="",
            llm_base_url="",
            llm_model="test",
            llm_max_tokens=100,
            llm_temperature=0.5,
            llm_enable_thinking=False,
            llm_timeout_seconds=10.0,
            embedding_api_key="",
            embedding_base_url="",
            embedding_model="test",
            embedding_dimensions=384,
        )

    async def asyncTearDown(self) -> None:
        model_config_service._runtime = self.original_runtime

    async def test_empty_notes_returns_empty(self):
        result = await llm_service.generate_quiz_from_notes("")
        self.assertEqual(result, [])

    async def test_short_notes_returns_empty(self):
        result = await llm_service.generate_quiz_from_notes("短")
        self.assertEqual(result, [])

    async def test_offline_returns_empty_list(self):
        """Without a real API key, the mock response should yield []."""
        notes = "一元二次方程的求根公式为 x = (-b ± √(b²-4ac)) / 2a，其中判别式 Δ = b²-4ac 决定根的性质。"
        result = await llm_service.generate_quiz_from_notes(notes, subject="数学", grade="高中")
        # Mock mode → no valid JSON quiz → empty list
        self.assertEqual(result, [])
        self.assertIsInstance(result, list)


class TestAIRefusal(unittest.IsolatedAsyncioTestCase):
    """Verify the orchestrator refuses to answer when no reliable context is retrieved."""

    async def asyncSetUp(self) -> None:
        self.original_settings = {
            "qdrant_path": settings.qdrant_path,
            "embedding_dimensions": settings.embedding_dimensions,
            "embedding_api_key": settings.embedding_api_key,
            "deepseek_api_key": settings.deepseek_api_key,
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
            Path(__file__).resolve().parent / "test_data" / "test_qdrant_refusal"
        )
        shutil.rmtree(self.test_qdrant_path, ignore_errors=True)
        settings.qdrant_path = str(self.test_qdrant_path)
        settings.embedding_dimensions = 384
        settings.embedding_api_key = ""
        settings.deepseek_api_key = ""
        model_config_service.reset_to_environment()
        rag_module._client = None

        # Create a test student (no resources seeded → empty retrieval)
        self.student = await student_profile_service.create_student(
            db=self.db, username="refusal_student", hashed_password="x",
            name="Refusal Test", subject="数学",
        )
        await self.db.commit()

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

    async def test_refusal_when_no_context(self):
        """When no resources are retrieved, the orchestrator should return a
        '资料不足' refusal without calling the LLM."""
        result = await orchestrator.handle_chat(
            db=self.db,
            student_id=self.student.id,
            message="请讲解量子力学的测不准原理",  # no matching resources in DB
        )
        await self.db.commit()

        # The response should indicate insufficient material
        response = result["response"]
        self.assertTrue(
            "资料不足" in response or "无法回答" in response or "没有找到" in response,
            f"Expected refusal message, got: {response[:200]}",
        )
        # References should be empty
        self.assertEqual(result["references"], [])

        # Verify a user message was logged
        messages = (
            await self.db.scalars(
                select(ChatMessage)
                .where(ChatMessage.session_id == result["session_id"])
                .order_by(ChatMessage.created_at.asc())
            )
        ).all()
        self.assertGreaterEqual(len(messages), 1)
        self.assertEqual(messages[0].role, "user")


if __name__ == "__main__":
    unittest.main()
