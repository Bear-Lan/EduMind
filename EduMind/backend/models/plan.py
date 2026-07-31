"""
EduMind LearningPlan Database Model

Defines the LearningPlan ORM entity and relationships.
"""

import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base


class LearningPlan(Base):
    """Represents a personalized study plan generated for a student."""

    __tablename__ = "learning_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id"),
        index=True,
        nullable=False,
    )
    target_topic: Mapped[str] = mapped_column(String(255), nullable=False)
    learning_steps: Mapped[dict | list | None] = mapped_column(
        JSON, nullable=True, default=list
    )
    recommendation_reason: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    ai_guide: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default="active", nullable=False
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="plans")
