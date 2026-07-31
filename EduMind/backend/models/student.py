"""
EduMind Student Database Models

Defines Student and StudentProfile ORM entities and relationships.
"""

import datetime
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base


class Student(Base):
    """Represents a student user in the system."""

    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    grade: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    # Relationships
    profile: Mapped["StudentProfile"] = relationship(
        "StudentProfile",
        back_populates="student",
        cascade="all, delete-orphan",
        uselist=False,
    )
    plans: Mapped[list["LearningPlan"]] = relationship(
        "LearningPlan",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    history: Mapped[list["LearningHistory"]] = relationship(
        "LearningHistory",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    sessions: Mapped[list["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="student",
        cascade="all, delete-orphan",
    )


class StudentProfile(Base):
    """Represents the current learning state/profile of a student."""

    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id"),
        unique=True,
        index=True,
        nullable=False,
    )
    current_goal: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mastery_map: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    learning_preferences: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, default=dict
    )
    last_recommendation: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, default=dict
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="profile")
