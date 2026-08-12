"""
EduMind LearningResource Database Model

Defines the LearningResource ORM entity.
Chunk-level rows carry parent_doc / chapter / section for RAG citations.
"""

import datetime
from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base


class LearningResource(Base):
    """Educational resource chunk used for RAG (one row ≈ one indexed chunk)."""

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
    )  # Chunk text retrieved during RAG

    # Chunk lineage / textbook location
    parent_doc: Mapped[str | None] = mapped_column(
        String(255), index=True, nullable=True
    )  # Logical parent document title
    chapter: Mapped[str | None] = mapped_column(String(255), nullable=True)
    section: Mapped[str | None] = mapped_column(String(255), nullable=True)
    chunk_index: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
