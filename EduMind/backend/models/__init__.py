"""
EduMind ORM Models Export Package

Imports all models to register them on the declarative metadata for Alembic.
"""

from database.base import Base
from models.student import Student, StudentProfile
from models.plan import LearningPlan
from models.history import LearningHistory
from models.chat import ChatSession, ChatMessage
from models.resource import LearningResource
from models.quiz import QuizQuestion, QuizAttempt
from models.admin import AdminUser, SystemModelConfig

__all__ = [
    "Base",
    "Student",
    "StudentProfile",
    "LearningPlan",
    "LearningHistory",
    "ChatSession",
    "ChatMessage",
    "LearningResource",
    "QuizQuestion",
    "QuizAttempt",
    "AdminUser",
    "SystemModelConfig",
]
