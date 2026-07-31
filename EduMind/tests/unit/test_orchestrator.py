"""
Unit Tests for Learning Orchestrator Module

Verifies end-to-end orchestration workflows (Chat, Plans, Assessments, and Task completions).
"""

import sys
import shutil
import unittest
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Add backend directory to sys.path so we can import local modules
backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from models import Base, LearningHistory, ChatSession, ChatMessage
from config.settings import settings
from student_profile import student_profile_service
from recommendation import recommendation_engine
from rag import rag_module
from application.orchestrator import orchestrator

# ── Shared mock curriculum ────────────────────────────────────────────────────
MOCK_CURRICULUM = {
    "__zh_names__": {
        "Basic Arithmetic":        "基础四则运算",
        "Introduction to Algebra": "代数初步",
        "Linear Equations":        "一元一次方程",
        "Quadratic Equations":     "二次方程",
        "Basic Geometry":          "基础几何",
        "Coordinate Geometry":     "解析几何",
    },
    "Basic Arithmetic":        [],
    "Introduction to Algebra": ["Basic Arithmetic"],
    "Linear Equations":        ["Introduction to Algebra"],
    "Quadratic Equations":     ["Linear Equations"],
    "Basic Geometry":          ["Basic Arithmetic"],
    "Coordinate Geometry":     ["Basic Geometry", "Linear Equations"],
}


class TestLearningOrchestrator(unittest.IsolatedAsyncioTestCase):
    """Asynchronous unit/integration tests for LearningOrchestrator."""

    async def asyncSetUp(self) -> None:
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

        # 2. Qdrant Setup (Local Path Mode, isolated per test run)
        self.test_qdrant_path = (
            Path(__file__).resolve().parent / "test_data" / "test_qdrant_orch"
        )
        settings.qdrant_path = str(self.test_qdrant_path)
        settings.embedding_dimensions = 384
        settings.deepseek_api_key = ""  # Force mock LLM

        rag_module._client = None

        # Seed textbook resource in Qdrant & SQLite for RAG query testing
        await rag_module.upsert_resource(
            db=self.db,
            title="Algebra Basics",
            subject="Mathematics",
            topic="Introduction to Algebra",
            content="Algebra uses variables like x and y.",
        )
        await self.db.commit()

        # 3. Seed test student with mock curriculum embedded in profile
        self.student = await student_profile_service.create_student(
            db=self.db,
            username="student_orch",
            hashed_password="password",
            name="Orchestrator Learner",
            subject="数学",
        )
        # Inject mock curriculum into student profile preferences
        profile = await student_profile_service.get_profile(self.db, self.student.id)
        from sqlalchemy.orm.attributes import flag_modified
        prefs = dict(profile.learning_preferences or {})
        prefs["curricula"] = {"数学": MOCK_CURRICULUM}
        profile.learning_preferences = prefs
        flag_modified(profile, "learning_preferences")
        await self.db.commit()

    async def asyncTearDown(self) -> None:
        await self.db.close()
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.engine.dispose()

        if rag_module._client:
            await rag_module._client.close()
            rag_module._client = None

        if self.test_qdrant_path.exists():
            shutil.rmtree(self.test_qdrant_path, ignore_errors=True)

    async def test_handle_chat_workflow(self) -> None:
        """Verify chat workflow resolves RAG, runs LLM, and logs messages to DB."""
        result = await orchestrator.handle_chat(
            db=self.db,
            student_id=self.student.id,
            message="Explain algebra variables please.",
        )
        await self.db.commit()

        # Output verification
        self.assertIsNotNone(result["session_id"])
        self.assertIn("[Mock AI Coach Response]", result["response"])
        self.assertEqual(len(result["references"]), 1)
        self.assertEqual(result["references"][0]["title"], "Algebra Basics")

        # Database logging verification
        session_id = result["session_id"]
        messages = (
            (
                await self.db.scalars(
                    select(ChatMessage)
                    .where(ChatMessage.session_id == session_id)
                    .order_by(ChatMessage.created_at.asc())
                )
            )
        ).all()

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].role, "user")
        self.assertEqual(messages[0].content, "Explain algebra variables please.")
        self.assertEqual(messages[1].role, "assistant")
        self.assertIn("[Mock AI Coach Response]", messages[1].content)

    async def test_handle_learning_plan_workflow(self) -> None:
        """Verify dynamic plan generation, active checks, and LLM guides."""
        # 1. Request plan (first time, none exists, triggers recommendation)
        result = await orchestrator.handle_learning_plan(self.db, self.student.id)
        await self.db.commit()

        self.assertIsNotNone(result["plan_id"])
        # target_topic should be one of the eligible root topics from the mock curriculum
        self.assertIsNotNone(result["target_topic"])
        self.assertEqual(len(result["learning_steps"]), 3)
        self.assertIn("[Mock AI Coach Response]", result["ai_guide"])

        plan_id_1 = result["plan_id"]

        # 2. Request plan again (returns same active plan, no duplicate creation)
        result2 = await orchestrator.handle_learning_plan(self.db, self.student.id)
        self.assertEqual(result2["plan_id"], plan_id_1)

    async def test_handle_assessment_workflow(self) -> None:
        """Verify assessment saves logs, updates mastery, and triggers next plan."""
        assessment_data = {
            "topic": "Basic Arithmetic",
            "score": 0.9,
            "duration": 500,
        }
        result = await orchestrator.handle_assessment(
            db=self.db, student_id=self.student.id, assessment_data=assessment_data
        )
        await self.db.commit()

        # Mastery mapping update check
        self.assertEqual(result["updated_mastery"].get("Basic Arithmetic"), 0.9)

        # Triggered next plan (Basic Arithmetic mastered → next eligible recommended)
        self.assertIsNotNone(result["new_plan_id"])
        self.assertIn(
            result["recommended_topic"],
            ["Introduction to Algebra", "Basic Geometry"]
        )

        # History log check
        history = await self.db.scalar(
            select(LearningHistory)
            .where(
                LearningHistory.student_id == self.student.id,
                LearningHistory.activity_type == "assessment",
            )
            .limit(1)
        )
        self.assertIsNotNone(history)
        self.assertEqual(history.topic, "Basic Arithmetic")
        self.assertEqual(history.duration, 500)
        self.assertEqual(history.result.get("score"), 0.9)

    async def test_handle_learning_completion_workflow(self) -> None:
        """Verify step completion check, profile progress update, and history logging."""
        # 1. Generate active plan directly via recommendation engine
        profile = await student_profile_service.get_profile(self.db, self.student.id)
        plan = await recommendation_engine.generate_learning_plan(
            self.db, profile, MOCK_CURRICULUM
        )
        await self.db.commit()

        # 2. Complete Step 1
        completion_data = {
            "plan_id": plan.id,
            "step_number": 1,
            "score": 0.5,
            "duration": 200,
        }
        result = await orchestrator.handle_learning_completion(
            db=self.db,
            student_id=self.student.id,
            completion_data=completion_data,
        )
        await self.db.commit()

        self.assertEqual(result["step_completed"], 1)
        self.assertFalse(result["all_steps_completed"])
        self.assertEqual(result["plan_status"], "active")
        self.assertAlmostEqual(result["current_mastery"].get(plan.target_topic), 1 / 3)

        # 3. Complete Steps 2 & 3 to trigger plan completion
        await orchestrator.handle_learning_completion(
            db=self.db,
            student_id=self.student.id,
            completion_data={"plan_id": plan.id, "step_number": 2, "score": 0.7, "duration": 150},
        )
        result3 = await orchestrator.handle_learning_completion(
            db=self.db,
            student_id=self.student.id,
            completion_data={"plan_id": plan.id, "step_number": 3, "score": 0.95, "duration": 300},
        )
        await self.db.commit()

        self.assertTrue(result3["all_steps_completed"])
        self.assertEqual(result3["plan_status"], "completed")

        # 4. Verify history logs
        logs = (
            (
                await self.db.scalars(
                    select(LearningHistory)
                    .where(
                        LearningHistory.student_id == self.student.id,
                        LearningHistory.activity_type == "learning_completion",
                    )
                    .order_by(LearningHistory.timestamp.desc())
                )
            )
        ).all()
        self.assertEqual(len(logs), 3)
        self.assertTrue(logs[0].result.get("all_steps_completed"))


if __name__ == "__main__":
    unittest.main()
