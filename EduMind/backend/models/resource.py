"""
EduMind LearningResource Database Model

Defines the LearningResource ORM entity.
"""

import datetime
from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base


class LearningResource(Base):
    """Represents an educational resource (curriculum context/textbook details) used for RAG."""

    __tablename__ = "learning_resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    embedding_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # Reference to Qdrant Vector ID
    content: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # Text content retrieved during RAG
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
