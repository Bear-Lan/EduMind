"""
EduMind Quiz Bank Models

Question bank + student attempt records.

Design:
- quiz_questions  — structured questions; AI only fills `explanation` lazily.
- quiz_attempts    — every submission is recorded for error-book / analytics.
"""

import datetime
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, JSON, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class QuizQuestion(Base):
    """A structured question in the question bank."""

    __tablename__ = "quiz_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    subject: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    topic: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    grade: Mapped[str | None] = mapped_column(String(50), nullable=True)

    difficulty: Mapped[int] = mapped_column(Integer, index=True, nullable=False)  # 1~5

    question_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # 'single_choice' | 'multiple_choice' | 'fill_blank' | 'short_answer' | 'true_false'

    stem: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # {"A": "...", "B": "..."}

    correct_answer: Mapped[dict] = mapped_column(JSON, nullable=False)
    # 单选/判断: {"answer":"B"}
    # 多选: {"answers":["A","C"]}
    # 填空: {"answer":"2x", "aliases":["2*x"]}
    # 简答: {"keywords":["判别式","Δ>0"], "sample":"…"}

    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)  # AI 生成的解析
    knowledge_tags: Mapped[list | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    attempts: Mapped[list["QuizAttempt"]] = relationship(
        "QuizAttempt", back_populates="question", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_quiz_subject_topic_diff", "subject", "topic", "difficulty"),
    )


class QuizAttempt(Base):
    """A student's submission on a single question."""

    __tablename__ = "quiz_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id"), index=True, nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quiz_questions.id"), index=True, nullable=False
    )

    subject: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    topic: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)

    user_answer: Mapped[dict] = mapped_column(JSON, nullable=False)
    # {"answer":"B"} / {"answers":["A","C"]} / {"text":"..."}

    is_correct: Mapped[bool] = mapped_column(Integer, nullable=False)  # 0/1
    score: Mapped[float] = mapped_column(Float, nullable=False)        # 0~1
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        index=True,
        nullable=False,
    )

    question: Mapped[QuizQuestion] = relationship("QuizQuestion", back_populates="attempts")