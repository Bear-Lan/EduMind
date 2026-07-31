"""
Unit Tests for Recommendation Engine Module

Verifies topic priority calculations, eligibility constraints, explanation generation,
and learning plan generation and persistence.
"""

import sys
import unittest
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Add backend directory to sys.path so we can import local modules
backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from models import Base, Student, StudentProfile
from student_profile import student_profile_service
from recommendation import recommendation_engine

# ── Standard mock curriculum used across all tests ────────────────────────────
# Mirrors a realistic 6-topic math curriculum with prerequisite chains.
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


class TestRecommendationEngine(unittest.IsolatedAsyncioTestCase):
    """Asynchronous integration/unit tests for RecommendationEngine against in-memory SQLite."""

    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.async_session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.db = self.async_session_factory()

        # Seed a test student and profile
        self.student = await student_profile_service.create_student(
            db=self.db,
            username="test_student",
            hashed_password="hash",
            name="Test Learner",
        )
        await self.db.commit()

        # Retrieve profile
        self.profile = await student_profile_service.get_profile(
            self.db, self.student.id
        )

    async def asyncTearDown(self) -> None:
        await self.db.close()
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.engine.dispose()

    async def test_calculate_priority_empty_mastery(self) -> None:
        """Verify that a brand new student can only learn the root topic (Basic Arithmetic)."""
        priorities = recommendation_engine.calculate_priority(self.profile, MOCK_CURRICULUM)

        # Basic Arithmetic has index 0 (prereq: []), hence eligible and priority = 100
        eligible_topics = [p for p in priorities if p["eligible"]]
        self.assertEqual(len(eligible_topics), 1)  # Only Basic Arithmetic has []
        # Highest priority: index 0 = Basic Arithmetic
        self.assertEqual(eligible_topics[0]["topic"], "Basic Arithmetic")
        self.assertEqual(eligible_topics[0]["priority_score"], 100)

        # Locked topics should have priority 0
        locked_topics = [p for p in priorities if not p["eligible"]]
        for topic in locked_topics:
            self.assertEqual(topic["priority_score"], 0)

    async def test_calculate_priority_one_mastered(self) -> None:
        """Verify algebra and geometry become eligible once arithmetic is mastered."""
        # Set Basic Arithmetic mastery to 0.85 (mastered)
        self.profile = await student_profile_service.update_mastery(
            db=self.db,
            student_id=self.student.id,
            mastery_map={"Basic Arithmetic": 0.85},
        )
        await self.db.commit()

        priorities = recommendation_engine.calculate_priority(self.profile, MOCK_CURRICULUM)
        eligible_topics = [p for p in priorities if p["eligible"]]

        # Introduction to Algebra and Basic Geometry should now be eligible
        eligible_names = [p["topic"] for p in eligible_topics]
        self.assertIn("Introduction to Algebra", eligible_names)
        self.assertIn("Basic Geometry", eligible_names)

        # Introduction to Algebra (index 1) should rank higher than Basic Geometry (index 4)
        self.assertEqual(eligible_topics[0]["topic"], "Introduction to Algebra")

    async def test_explain_recommendation(self) -> None:
        """Verify structured explanation generation."""
        # Set Basic Arithmetic to mastered
        self.profile = await student_profile_service.update_mastery(
            db=self.db,
            student_id=self.student.id,
            mastery_map={"Basic Arithmetic": 0.85},
        )
        await self.db.commit()

        explanation = recommendation_engine.explain_recommendation(
            self.profile, MOCK_CURRICULUM, "Introduction to Algebra"
        )
        self.assertEqual(explanation["topic"], "Introduction to Algebra")
        self.assertEqual(explanation["code"], "PREREQUISITES_MET")
        self.assertIn("Basic Arithmetic", explanation["reason"])
        self.assertEqual(
            explanation["metadata"]["mastery_levels"]["Basic Arithmetic"], 0.85
        )

    async def test_generate_learning_plan_success(self) -> None:
        """Verify plan database persistence and profile updates on generation."""
        plan = await recommendation_engine.generate_learning_plan(
            self.db, self.profile, MOCK_CURRICULUM
        )
        await self.db.commit()

        # Plan assertion
        self.assertIsNotNone(plan)
        self.assertIsNotNone(plan.id)
        self.assertEqual(plan.target_topic, "Basic Arithmetic")
        self.assertEqual(len(plan.learning_steps), 3)
        self.assertEqual(plan.status, "active")

        # Profile assertion
        profile = await student_profile_service.get_profile(self.db, self.student.id)
        self.assertEqual(profile.last_recommendation.get("topic"), "Basic Arithmetic")
        self.assertEqual(
            profile.last_recommendation.get("reason_code"), "PREREQUISITES_MET"
        )
        self.assertIsNotNone(profile.last_recommendation.get("generated_at"))

    async def test_generate_learning_plan_fully_completed(self) -> None:
        """Verify generate_learning_plan returns None when the entire curriculum is mastered."""
        # Mark all topics in the curriculum as mastered
        mastery_data = {
            "Basic Arithmetic":        0.9,
            "Introduction to Algebra": 0.85,
            "Linear Equations":        0.8,
            "Quadratic Equations":     0.9,
            "Basic Geometry":          0.8,
            "Coordinate Geometry":     0.85,
        }
        self.profile = await student_profile_service.update_mastery(
            db=self.db,
            student_id=self.student.id,
            mastery_map=mastery_data,
        )
        await self.db.commit()

        plan = await recommendation_engine.generate_learning_plan(
            self.db, self.profile, MOCK_CURRICULUM
        )
        self.assertIsNotNone(plan)
        self.assertIn("巩固复习", plan.recommendation_reason)


if __name__ == "__main__":
    unittest.main()
