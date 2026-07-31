"""
Unit Tests for Student Profile Module

Verifies all CRUD, goal, preference, mastery map, and progress tracking operations.
"""

import sys
import os
import unittest
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Add backend directory to sys.path so we can import local modules
backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from models import Base
from student_profile import student_profile_service
from core.exceptions import NotFoundError, ValidationError


class TestStudentProfileService(unittest.IsolatedAsyncioTestCase):
    """Asynchronous integration/unit tests for StudentProfileService against in-memory SQLite."""

    async def asyncSetUp(self) -> None:
        # Create an in-memory SQLite database for testing async database transactions
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.async_session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create all tables on setup
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.db = self.async_session_factory()

    async def asyncTearDown(self) -> None:
        await self.db.close()
        # Drop all tables on teardown
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.engine.dispose()

    async def test_create_student_and_profile(self) -> None:
        """Verify that creating a student also initializes a default profile successfully."""
        student = await student_profile_service.create_student(
            db=self.db,
            username="test_user",
            hashed_password="mock_hashed_password",
            name="Test Student",
            grade="Grade 10",
            subject="Mathematics",
            target_score=95.0,
        )
        await self.db.commit()

        # Assert Student values
        self.assertIsNotNone(student.id)
        self.assertEqual(student.username, "test_user")
        self.assertEqual(student.name, "Test Student")
        self.assertEqual(student.grade, "Grade 10")
        self.assertEqual(student.subject, "Mathematics")
        self.assertEqual(student.target_score, 95.0)

        # Assert StudentProfile was auto-initialized
        profile = await student_profile_service.get_profile(self.db, student.id)
        self.assertIsNotNone(profile.id)
        self.assertEqual(profile.student_id, student.id)
        self.assertEqual(profile.mastery_map, {})
        self.assertEqual(profile.learning_preferences, {})

    async def test_create_duplicate_username(self) -> None:
        """Verify that creating a student with a duplicate username raises ValidationError."""
        await student_profile_service.create_student(
            db=self.db,
            username="test_user",
            hashed_password="hashed_pass",
            name="Student A",
        )
        await self.db.commit()

        with self.assertRaises(ValidationError) as ctx:
            await student_profile_service.create_student(
                db=self.db,
                username="test_user",
                hashed_password="another_pass",
                name="Student B",
            )
        self.assertIn("already taken", str(ctx.exception))

    async def test_get_nonexistent_student(self) -> None:
        """Verify that querying a nonexistent student profile raises NotFoundError."""
        with self.assertRaises(NotFoundError) as ctx:
            await student_profile_service.get_profile(self.db, 999)
        self.assertEqual(ctx.exception.code, 404)

    async def test_update_profile(self) -> None:
        """Verify updating student profile current goals and preferences."""
        student = await student_profile_service.create_student(
            db=self.db,
            username="test_user",
            hashed_password="hashed_pass",
            name="Student A",
        )
        await self.db.commit()

        # Update goal and preferences
        updated_profile = await student_profile_service.update_profile(
            db=self.db,
            student_id=student.id,
            goal="Score 90+ in Algebra",
            preferences={"pace": "fast"},
        )
        await self.db.commit()

        self.assertEqual(updated_profile.current_goal, "Score 90+ in Algebra")
        self.assertEqual(updated_profile.learning_preferences, {"pace": "fast"})

        # Merge secondary preference updates
        merged_profile = await student_profile_service.update_profile(
            db=self.db,
            student_id=student.id,
            preferences={"style": "visual"},
        )
        await self.db.commit()

        self.assertEqual(
            merged_profile.learning_preferences,
            {"pace": "fast", "style": "visual"},
        )

    async def test_update_mastery(self) -> None:
        """Verify updating and merging mastery maps."""
        student = await student_profile_service.create_student(
            db=self.db,
            username="test_user",
            hashed_password="hashed_pass",
            name="Student A",
        )
        await self.db.commit()

        # Set initial mastery values
        profile = await student_profile_service.update_mastery(
            db=self.db,
            student_id=student.id,
            mastery_map={"algebra": 0.8},
        )
        await self.db.commit()
        self.assertEqual(profile.mastery_map, {"algebra": 0.8})

        # Merge updates
        profile = await student_profile_service.update_mastery(
            db=self.db,
            student_id=student.id,
            mastery_map={"geometry": 0.6, "algebra": 0.85},
        )
        await self.db.commit()
        self.assertEqual(profile.mastery_map, {"algebra": 0.85, "geometry": 0.6})

    async def test_update_learning_progress(self) -> None:
        """Verify registering learning progress updates the mastery map correctly."""
        student = await student_profile_service.create_student(
            db=self.db,
            username="test_user",
            hashed_password="hashed_pass",
            name="Student A",
        )
        await self.db.commit()

        # Record progress for a topic
        profile = await student_profile_service.update_learning_progress(
            db=self.db,
            student_id=student.id,
            progress_data={"topic": "Calculus I", "score": 0.95},
        )
        await self.db.commit()

        self.assertEqual(profile.mastery_map.get("Calculus I"), 0.95)

        # Invalid progress data check
        with self.assertRaises(ValidationError):
            await student_profile_service.update_learning_progress(
                db=self.db,
                student_id=student.id,
                progress_data={"score": 0.9},  # Missing topic
            )


if __name__ == "__main__":
    unittest.main()
