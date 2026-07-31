"""
EduMind LearningHistory Database Model

Defines the LearningHistory ORM entity and relationships.
"""

import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base


class LearningHistory(Base):
    """Represents a historical learning activity completed by a student."""

    __tablename__ = "learning_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id"),
        index=True,
        nullable=False,
    )
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    duration: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )  # study duration in seconds
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="history")
