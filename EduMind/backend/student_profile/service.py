"""
EduMind Student Profile Service

Handles core business logic for student profiles, preferences, and knowledge mastery maps.
"""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.student import Student, StudentProfile
from models.plan import LearningPlan
from core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class StudentProfileService:
    """Business logic service for managing students and student profiles."""

    async def create_student(
        self,
        db: AsyncSession,
        username: str,
        hashed_password: str,
        name: str,
        grade: str | None = None,
        subject: str | None = None,
        target_score: float | None = None,
    ) -> Student:
        """
        Create a new student and automatically initialize a default profile.

        Raises ValidationError if the username is already taken.
        """
        # Verify username uniqueness
        username_exists = await db.scalar(
            select(Student.id).where(Student.username == username)
        )
        if username_exists:
            raise ValidationError(f"Username '{username}' is already taken")

        student = Student(
            username=username,
            hashed_password=hashed_password,
            name=name,
            grade=grade,
            subject=subject,
            target_score=target_score,
        )
        db.add(student)
        await db.flush()  # Generate student ID

        # Auto-initialize profile with constructed goal if fields present
        goal = None
        if grade or subject or target_score is not None:
            parts = []
            if grade and subject:
                parts.append(f"{grade} {subject}")
            elif grade:
                parts.append(grade)
            elif subject:
                parts.append(subject)
            if target_score is not None:
                parts.append(f"(Target: {target_score})")
            goal = " ".join(parts)

        await self.create_profile(db, student_id=student.id, goal=goal)

        logger.info(
            f"Created student ID {student.id} (username: {username}) with default profile"
        )
        return student

    async def get_profile(self, db: AsyncSession, student_id: int) -> StudentProfile:
        """
        Retrieve a student's profile.

        Raises NotFoundError if the student or profile does not exist.
        """
        # Ensure student exists first
        student_exists = await db.scalar(
            select(Student.id).where(Student.id == student_id)
        )
        if not student_exists:
            raise NotFoundError("Student", str(student_id))

        profile = await db.scalar(
            select(StudentProfile).where(StudentProfile.student_id == student_id)
        )
        if not profile:
            raise NotFoundError("StudentProfile", str(student_id))

        return profile

    async def create_profile(
        self,
        db: AsyncSession,
        student_id: int,
        goal: str | None = None,
        preferences: dict | None = None,
    ) -> StudentProfile:
        """
        Create a new profile for an existing student.

        Raises ValidationError if a profile already exists for the student.
        """
        # Verify student exists
        student_exists = await db.scalar(
            select(Student.id).where(Student.id == student_id)
        )
        if not student_exists:
            raise NotFoundError("Student", str(student_id))

        # Verify profile does not already exist
        existing_profile = await db.scalar(
            select(StudentProfile.id).where(
                StudentProfile.student_id == student_id
            )
        )
        if existing_profile:
            raise ValidationError(
                f"Profile for student ID {student_id} already exists"
            )

        profile = StudentProfile(
            student_id=student_id,
            current_goal=goal,
            learning_preferences=preferences or {},
            mastery_map={},
            last_recommendation={},
        )
        db.add(profile)
        await db.flush()

        logger.info(f"Created profile ID {profile.id} for student ID {student_id}")
        return profile

    async def update_profile(
        self,
        db: AsyncSession,
        student_id: int,
        goal: str | None = None,
        subject: str | None = None,
        preferences: dict | None = None,
        runtime_api_key: str = "",
    ) -> StudentProfile:
        """
        Update general profile goals and preferences.
        """
        profile = await self.get_profile(db, student_id)
        student = await db.scalar(select(Student).where(Student.id == student_id))

        if subject:
            is_subject_changed = (student.subject != subject)
            
            # 1. First fetch or generate the curriculum, which involves network calls
            if not goal:
                grade = student.grade or ""
                goal = f"{grade} {subject}".strip()

            curriculum_key = goal or subject
            prefs = dict(profile.learning_preferences or {})
            curricula = prefs.get("curricula", {})
            if subject not in curricula or len(curricula.get(subject, {}).get("__zh_names__", {})) <= 6:
                from llm import llm_service
                logger.info(f"Generating rich dynamic curriculum for: {curriculum_key}")
                new_curriculum = await llm_service.generate_curriculum(curriculum_key, runtime_api_key)
                curricula[subject] = new_curriculum
                prefs["curricula"] = curricula
                profile.learning_preferences = prefs
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(profile, "learning_preferences")

            # 2. Now perform the fast synchronous entity updates
            student.subject = subject
            if not goal:
                grade = student.grade or ""
                goal = f"{grade} {subject}".strip()

            if is_subject_changed:
                # Suspend active plans from previous subject so new one generates
                active_plans = await db.scalars(
                    select(LearningPlan)
                    .where(
                        LearningPlan.student_id == student_id,
                        LearningPlan.status == "active"
                    )
                )
                for plan in active_plans:
                    plan.status = "suspended"
                    logger.info(f"Suspended active LearningPlan {plan.id} due to subject switch")


        if goal is not None:
            profile.current_goal = goal

        if preferences is not None:
            current_prefs = dict(profile.learning_preferences or {})
            current_prefs.update(preferences)
            profile.learning_preferences = current_prefs

        await db.flush()
        logger.info(f"Updated profile goals/preferences for student ID {student_id}")
        return profile

    async def update_mastery(
        self, db: AsyncSession, student_id: int, mastery_map: dict
    ) -> StudentProfile:
        """
        Merge new knowledge points and mastery rates into the mastery map.
        """
        profile = await self.get_profile(db, student_id)

        # Merge mastery maps
        current_mastery = dict(profile.mastery_map or {})
        current_mastery.update(mastery_map)
        profile.mastery_map = current_mastery

        await db.flush()
        logger.info(f"Updated mastery map for student ID {student_id}")
        return profile

    async def update_learning_progress(
        self, db: AsyncSession, student_id: int, progress_data: dict
    ) -> StudentProfile:
        """
        Record completed learning progress. Updates mastery map based on the completed topic score.
        """
        topic = progress_data.get("topic")
        if not topic:
            raise ValidationError("progress_data must contain 'topic'")

        score = progress_data.get("score", 0.0)

        # Update mastery map based on the learning progress
        profile = await self.get_profile(db, student_id)
        current_mastery = dict(profile.mastery_map or {})
        current_mastery[topic] = float(score)
        profile.mastery_map = current_mastery

        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(profile, "mastery_map")

        await db.flush()
        logger.info(
            f"Recorded learning progress on '{topic}' (score: {score}) for student ID {student_id}"
        )
        return profile
