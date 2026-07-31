"""
EduMind ORM Declarative Base

All ORM models must inherit from Base defined here.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all EduMind ORM models."""
    pass
